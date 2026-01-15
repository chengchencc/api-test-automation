import json
import time
import hashlib
import base64
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import requests
from datetime import datetime, timedelta
from src.config.logger import logger
from src.config.configuration import project_config


class OAuth2Token:
    """OAuth 2.0令牌类"""

    def __init__(self,
                 access_token: str,
                 token_type: str = "Bearer",
                 expires_in: int = 3600,
                 refresh_token: str = None,
                 scope: str = None,
                 created_at: float = None):
        """
        初始化令牌

        Args:
            access_token: 访问令牌
            token_type: 令牌类型，默认为Bearer
            expires_in: 过期时间（秒）
            refresh_token: 刷新令牌
            scope: 授权范围
            created_at: 创建时间戳
        """
        self.access_token = access_token
        self.token_type = token_type
        self.expires_in = expires_in
        self.refresh_token = refresh_token
        self.scope = scope
        self.created_at = created_at or time.time()

    @property
    def expires_at(self) -> float:
        """获取过期时间戳"""
        return self.created_at + self.expires_in

    @property
    def is_expired(self) -> bool:
        """检查令牌是否过期"""
        # 添加阈值，提前5分钟认为过期
        threshold = project_config.OAUTH2_TOKEN_EXPIRY_THRESHOLD
        return time.time() > (self.expires_at - threshold)

    @property
    def is_valid(self) -> bool:
        """检查令牌是否有效"""
        return bool(self.access_token) and not self.is_expired

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "refresh_token": self.refresh_token,
            "scope": self.scope,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OAuth2Token':
        """从字典创建令牌"""
        return cls(
            access_token=data.get("access_token", ""),
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in", 3600),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope"),
            created_at=data.get("created_at", time.time())
        )

    def get_auth_header(self) -> Dict[str, str]:
        """获取认证头"""
        if not self.access_token:
            return {}
        return {"Authorization": f"{self.token_type} {self.access_token}"}


class OAuth2Client:
    """OAuth 2.0客户端"""

    def __init__(self,
                 token_url: str = None,
                 client_id: str = None,
                 client_secret: str = None,
                 scope: list = None,
                 grant_type: str = None,
                 username: str = None,
                 password: str = None,
                 auth_url: str = None,
                 redirect_uri: str = None,
                 auto_refresh: bool = True):
        """
        初始化OAuth 2.0客户端

        Args:
            token_url: 令牌端点URL
            client_id: 客户端ID
            client_secret: 客户端密钥
            scope: 授权范围
            grant_type: 授权类型
            username: 用户名（密码模式）
            password: 密码（密码模式）
            auth_url: 授权端点URL
            redirect_uri: 重定向URI
            auto_refresh: 是否自动刷新令牌
        """
        self.token_url = token_url or project_config.OAUTH2_TOKEN_URL
        self.client_id = client_id or project_config.OAUTH2_CLIENT_ID
        self.client_secret = client_secret or project_config.OAUTH2_CLIENT_SECRET
        self.scope = scope or project_config.OAUTH2_SCOPE
        self.grant_type = grant_type or project_config.OAUTH2_GRANT_TYPE
        self.username = username or project_config.OAUTH2_USERNAME
        self.password = password or project_config.OAUTH2_PASSWORD
        self.auth_url = auth_url or project_config.OAUTH2_AUTH_URL
        self.redirect_uri = redirect_uri
        self.auto_refresh = auto_refresh

        # 会话
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "OAuth2Client/1.0",
            "Accept": "application/json"
        })

        # 令牌
        self._token: Optional[OAuth2Token] = None

        # 从缓存加载令牌
        self._load_token_from_cache()

    def _get_basic_auth_header(self) -> str:
        """获取基本认证头"""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def _get_token_request_data(self, grant_type: str = None, **kwargs) -> Dict[str, str]:
        """获取令牌请求数据"""
        grant_type = grant_type or self.grant_type

        data = {
            "grant_type": grant_type,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        if self.scope:
            data["scope"] = " ".join(self.scope)

        # 根据授权类型添加参数
        if grant_type == "password":
            data.update({
                "username": self.username,
                "password": self.password
            })
        elif grant_type == "client_credentials":
            # 客户端凭证模式不需要额外参数
            pass
        elif grant_type == "authorization_code":
            data.update({
                "code": kwargs.get("code"),
                "redirect_uri": kwargs.get("redirect_uri", self.redirect_uri)
            })
        elif grant_type == "refresh_token":
            if self._token and self._token.refresh_token:
                data.update({
                    "refresh_token": self._token.refresh_token
                })
            else:
                raise ValueError("没有可用的刷新令牌")

        # 添加额外参数
        data.update(kwargs)

        return {k: v for k, v in data.items() if v is not None}

    def request_token(self, grant_type: str = None, **kwargs) -> OAuth2Token:
        """
        请求令牌

        Args:
            grant_type: 授权类型
            **kwargs: 额外参数

        Returns:
            OAuth2Token对象
        """
        grant_type = grant_type or self.grant_type

        # 准备请求数据
        data = self._get_token_request_data(grant_type, **kwargs)

        # 准备请求头
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # 对于客户端凭证模式，使用Basic认证
        if grant_type == "client_credentials":
            headers["Authorization"] = self._get_basic_auth_header()
            # 移除client_id和client_secret参数
            data.pop("client_id", None)
            data.pop("client_secret", None)

        logger.info(f"请求OAuth 2.0令牌，授权类型: {grant_type}")

        try:
            # 发送请求
            response = self.session.post(
                self.token_url,
                data=data,
                headers=headers,
                timeout=project_config.TIMEOUT,
                verify=project_config.VERIFY_SSL
            )

            # 检查响应
            if response.status_code == 200:
                token_data = response.json()

                # 创建令牌对象
                self._token = OAuth2Token(
                    access_token=token_data.get("access_token"),
                    token_type=token_data.get("token_type", "Bearer"),
                    expires_in=token_data.get("expires_in", 3600),
                    refresh_token=token_data.get("refresh_token"),
                    scope=token_data.get("scope"),
                    created_at=time.time()
                )

                # 保存令牌到缓存
                self._save_token_to_cache()

                logger.info(f"获取令牌成功，过期时间: {self._token.expires_at}")
                return self._token
            else:
                error_msg = f"获取令牌失败: {response.status_code} {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except requests.exceptions.RequestException as e:
            logger.error(f"请求令牌异常: {e}")
            raise

    def refresh_token(self) -> OAuth2Token:
        """刷新令牌"""
        if not self._token or not self._token.refresh_token:
            logger.warning("没有可用的刷新令牌，尝试重新获取")
            return self.request_token()

        logger.info("刷新OAuth 2.0令牌")
        return self.request_token(grant_type="refresh_token")

    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        获取访问令牌

        Args:
            force_refresh: 是否强制刷新令牌

        Returns:
            访问令牌
        """
        # 如果没有令牌，则获取
        if not self._token:
            self.request_token()

        # 如果强制刷新或令牌过期，则刷新
        if force_refresh or (self.auto_refresh and self._token.is_expired):
            try:
                self.refresh_token()
            except Exception as e:
                logger.warning(f"刷新令牌失败: {e}")
                # 刷新失败，尝试重新获取
                self.request_token()

        return self._token.access_token if self._token else None

    def get_auth_header(self) -> Dict[str, str]:
        """获取认证头"""
        token = self.get_access_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def revoke_token(self, token: str = None, token_type_hint: str = "access_token"):
        """撤销令牌"""
        revoke_url = project_config.OAUTH2_REVOKE_URL

        if not revoke_url:
            logger.warning("未配置令牌撤销URL")
            return

        data = {
            "token": token or self.get_access_token(),
            "token_type_hint": token_type_hint,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        try:
            response = self.session.post(
                revoke_url,
                data=data,
                timeout=project_config.TIMEOUT,
                verify=project_config.VERIFY_SSL
            )

            if response.status_code in [200, 204]:
                logger.info("令牌撤销成功")
                self._token = None
                self._clear_token_cache()
            else:
                logger.warning(f"令牌撤销失败: {response.status_code}")

        except Exception as e:
            logger.error(f"令牌撤销异常: {e}")

    def introspect_token(self, token: str = None, token_type_hint: str = "access_token") -> Dict:
        """检查令牌"""
        introspect_url = project_config.OAUTH2_INTROSPECT_URL

        if not introspect_url:
            logger.warning("未配置令牌检查URL")
            return {}

        data = {
            "token": token or self.get_access_token(),
            "token_type_hint": token_type_hint,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        try:
            response = self.session.post(
                introspect_url,
                data=data,
                timeout=project_config.TIMEOUT,
                verify=project_config.VERIFY_SSL
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"令牌检查失败: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"令牌检查异常: {e}")
            return {}

    def _get_cache_key(self) -> str:
        """获取缓存键"""
        # 基于客户端ID、用户名和授权类型生成缓存键
        key_parts = [self.client_id, self.grant_type]
        if self.grant_type == "password":
            key_parts.append(self.username)

        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _save_token_to_cache(self):
        """保存令牌到缓存"""
        if not self._token or not project_config.OAUTH2_TOKEN_CACHE_FILE:
            return

        try:
            # 读取现有缓存
            cache_data = {}
            if project_config.OAUTH2_TOKEN_CACHE_FILE.exists():
                with open(project_config.OAUTH2_TOKEN_CACHE_FILE, 'r') as f:
                    cache_data = json.load(f)

            # 更新缓存
            cache_key = self._get_cache_key()
            cache_data[cache_key] = self._token.to_dict()

            # 写入文件
            with open(project_config.OAUTH2_TOKEN_CACHE_FILE, 'w') as f:
                json.dump(cache_data, f, indent=2)

            logger.debug(f"令牌已保存到缓存: {cache_key}")

        except Exception as e:
            logger.error(f"保存令牌到缓存失败: {e}")

    def _load_token_from_cache(self):
        """从缓存加载令牌"""
        if not project_config.OAUTH2_TOKEN_CACHE_FILE.exists():
            return

        try:
            with open(project_config.OAUTH2_TOKEN_CACHE_FILE, 'r') as f:
                cache_data = json.load(f)

            cache_key = self._get_cache_key()
            if cache_key in cache_data:
                token_data = cache_data[cache_key]
                self._token = OAuth2Token.from_dict(token_data)

                # 检查令牌是否过期
                if self._token.is_expired:
                    logger.info("缓存中的令牌已过期")
                    self._token = None
                else:
                    logger.debug(f"从缓存加载令牌: {cache_key}")

        except Exception as e:
            logger.error(f"从缓存加载令牌失败: {e}")

    def _clear_token_cache(self):
        """清除令牌缓存"""
        if project_config.OAUTH2_TOKEN_CACHE_FILE.exists():
            try:
                # 只清除当前客户端的令牌
                cache_key = self._get_cache_key()

                with open(project_config.OAUTH2_TOKEN_CACHE_FILE, 'r') as f:
                    cache_data = json.load(f)

                if cache_key in cache_data:
                    del cache_data[cache_key]

                    with open(project_config.OAUTH2_TOKEN_CACHE_FILE, 'w') as f:
                        json.dump(cache_data, f, indent=2)

                    logger.debug(f"已清除缓存中的令牌: {cache_key}")

            except Exception as e:
                logger.error(f"清除令牌缓存失败: {e}")

    def clear_token(self):
        """清除令牌"""
        self._token = None
        self._clear_token_cache()
        logger.info("令牌已清除")


# 全局OAuth 2.0客户端实例
oauth2_client = OAuth2Client()
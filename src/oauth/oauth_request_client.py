import requests
import json
import time
from typing import Dict, Any, Optional, Union, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from src.config.logger import logger, TestLogger
from src.config.settings import project_config as config
from src.common.template_engine_manager import template_engine
from .oauth2_client import oauth2_client, OAuth2Client


class OAuth2Auth(requests.auth.AuthBase):
    """OAuth 2.0认证类"""

    def __init__(self, oauth_client: OAuth2Client = None, force_refresh: bool = False):
        """
        初始化OAuth 2.0认证

        Args:
            oauth_client: OAuth 2.0客户端
            force_refresh: 是否强制刷新令牌
        """
        self.oauth_client = oauth_client or oauth2_client
        self.force_refresh = force_refresh

    def __call__(self, request):
        """添加认证头到请求"""
        if not config.OAUTH2_ENABLED:
            return request

        try:
            # 获取访问令牌
            access_token = self.oauth_client.get_access_token(force_refresh=self.force_refresh)
            if access_token:
                request.headers["Authorization"] = f"Bearer {access_token}"
        except Exception as e:
            logger.warning(f"获取OAuth 2.0令牌失败: {e}")

        return request


class RequestClient:
    """HTTP请求客户端（支持OAuth 2.0和模板）"""

    def __init__(self,
                 base_url: str = None,
                 timeout: int = None,
                 max_retries: int = None,
                 default_headers: Dict[str, str] = None,
                 use_oauth2: bool = None,
                 oauth_client: OAuth2Client = None):
        """
        初始化请求客户端

        Args:
            base_url: 基础URL
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            default_headers: 默认请求头
            use_oauth2: 是否使用OAuth 2.0
            oauth_client: OAuth 2.0客户端
        """
        self.base_url = base_url or config.BASE_URL
        self.timeout = timeout or config.TIMEOUT
        self.max_retries = max_retries or config.MAX_RETRY
        self.use_oauth2 = use_oauth2 if use_oauth2 is not None else config.OAUTH2_ENABLED
        self.oauth_client = oauth_client or oauth2_client

        # 创建会话
        self.session = requests.Session()
        self.test_logger = TestLogger("RequestClient")

        # 设置重试策略
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[401, 429, 500, 502, 503, 504],  # 401: 未授权
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 设置默认请求头
        self.default_headers = {
            'User-Agent': 'ApiTestFramework/2.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

        if default_headers:
            self.default_headers.update(default_headers)

        self.session.headers.update(self.default_headers)

        # 认证处理器
        self.auth_handlers = []

        # 响应钩子
        self.response_hooks = []
        self.request_hooks = []

        # 设置OAuth 2.0认证
        if self.use_oauth2 and self.oauth_client:
            self.add_auth_handler(OAuth2Auth(self.oauth_client))

        logger.info(f"初始化请求客户端，基础URL: {self.base_url}, OAuth 2.0: {self.use_oauth2}")

    def add_auth_handler(self, auth_handler):
        """添加认证处理器"""
        self.auth_handlers.append(auth_handler)

    def clear_auth_handlers(self):
        """清除认证处理器"""
        self.auth_handlers.clear()

    def add_response_hook(self, hook_func):
        """添加响应钩子"""
        self.response_hooks.append(hook_func)

    def add_request_hook(self, hook_func):
        """添加请求钩子"""
        self.request_hooks.append(hook_func)

    def _run_request_hooks(self, request_kwargs: Dict):
        """执行请求钩子"""
        for hook in self.request_hooks:
            try:
                hook(request_kwargs)
            except Exception as e:
                logger.error(f"请求钩子执行失败: {e}")

    def _run_response_hooks(self, response: requests.Response):
        """执行响应钩子"""
        for hook in self.response_hooks:
            try:
                hook(response)
            except Exception as e:
                logger.error(f"响应钩子执行失败: {e}")

    def _apply_auth_handlers(self, request_kwargs: Dict):
        """应用认证处理器"""
        for auth_handler in self.auth_handlers:
            if 'auth' not in request_kwargs:
                request_kwargs['auth'] = auth_handler
            else:
                # 如果已有认证，创建组合认证
                from requests.auth import AuthBase

                class CombinedAuth(AuthBase):
                    def __init__(self, *handlers):
                        self.handlers = handlers

                    def __call__(self, request):
                        for handler in self.handlers:
                            request = handler(request)
                        return request

                if isinstance(request_kwargs['auth'], AuthBase):
                    request_kwargs['auth'] = CombinedAuth(request_kwargs['auth'], auth_handler)

    def _handle_oauth2_token_refresh(self, response: requests.Response, request_kwargs: Dict) -> bool:
        """处理OAuth 2.0令牌刷新"""
        if not self.use_oauth2 or response.status_code != 401:
            return False

        # 检查是否是令牌过期
        try:
            response_json = response.json()
            error = response_json.get('error', '').lower()

            if error in ['invalid_token', 'expired_token', 'invalid_grant']:
                logger.info("检测到令牌过期，尝试刷新令牌")

                # 尝试刷新令牌
                try:
                    self.oauth_client.refresh_token()

                    # 更新认证头
                    for auth_handler in self.auth_handlers:
                        if isinstance(auth_handler, OAuth2Auth):
                            auth_handler.force_refresh = True

                    return True
                except Exception as e:
                    logger.error(f"刷新令牌失败: {e}")
                    return False
        except:
            pass

        return False

    def _prepare_request(self,
                         method: str,
                         url: str,
                         headers: Optional[Dict] = None,
                         params: Optional[Dict] = None,
                         json_data: Optional[Dict] = None,
                         data: Optional[Any] = None,
                         files: Optional[Dict] = None,
                         auth: Optional[Any] = None,
                         context: Optional[Dict] = None,
                         **kwargs) -> Tuple[str, Dict]:
        """
        准备请求参数

        Args:
            method: 请求方法
            url: 请求URL
            headers: 请求头
            params: URL参数
            json_data: JSON数据
            data: Form数据
            files: 文件
            auth: 认证
            context: 模板上下文
            **kwargs: 其他参数

        Returns:
            (处理后的URL, 请求参数)
        """
        # 渲染模板
        render_context = context or {}

        # 渲染URL
        if isinstance(url, str) and url:
            url = template_engine.render_string(url, **render_context)

        # 构建完整URL
        if url and not url.startswith(('http://', 'https://')):
            url = f"{self.base_url}{url}"

        # 准备请求数据
        request_kwargs = {
            'method': method.upper(),
            'url': url,
            'timeout': self.timeout,
            'verify': config.VERIFY_SSL,
            **kwargs
        }

        # 处理认证
        if auth:
            request_kwargs['auth'] = auth

        # 处理请求头
        if headers:
            rendered_headers = {}
            for k, v in headers.items():
                if isinstance(v, str):
                    rendered_headers[k] = template_engine.render_string(v, **render_context)
                else:
                    rendered_headers[k] = v
            request_kwargs['headers'] = {**self.session.headers, **rendered_headers}
        else:
            request_kwargs['headers'] = self.session.headers.copy()

        # 处理参数
        if params:
            rendered_params = template_engine.render(params, render_context)
            request_kwargs['params'] = rendered_params

        # 处理JSON数据
        if json_data is not None:
            rendered_json = template_engine.render(json_data, render_context)
            request_kwargs['json'] = rendered_json

        # 处理Form数据
        if data is not None:
            if isinstance(data, dict):
                rendered_data = template_engine.render(data, render_context)
                request_kwargs['data'] = rendered_data
            else:
                request_kwargs['data'] = data

        # 处理文件
        if files:
            request_kwargs['files'] = files

        return url, request_kwargs

    def send_request(self,
                     method: str,
                     url: str,
                     headers: Optional[Dict] = None,
                     params: Optional[Dict] = None,
                     json_data: Optional[Dict] = None,
                     data: Optional[Any] = None,
                     files: Optional[Dict] = None,
                     auth: Optional[Any] = None,
                     context: Optional[Dict] = None,
                     retry_on_oauth_failure: bool = True,
                     **kwargs) -> requests.Response:
        """发送HTTP请求"""

        start_time = time.time()
        retry_count = 0
        max_retries = 1 if retry_on_oauth_failure else 0

        while retry_count <= max_retries:
            try:
                # 准备请求
                full_url, request_kwargs = self._prepare_request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json_data=json_data,
                    data=data,
                    files=files,
                    auth=auth,
                    context=context,
                    **kwargs
                )

                # 应用认证处理器
                self._apply_auth_handlers(request_kwargs)

                # 执行请求钩子
                self._run_request_hooks(request_kwargs)

                # 记录请求
                self.test_logger.log_request(
                    method=method,
                    url=full_url,
                    data=json_data or data,
                    headers=request_kwargs.get('headers')
                )

                # 发送请求
                response = self.session.request(**request_kwargs)
                elapsed = time.time() - start_time

                # 添加响应时间
                response.elapsed = type('obj', (object,), {'total_seconds': lambda: elapsed})()

                # 记录响应
                self.test_logger.log_response(response)

                # 处理OAuth 2.0令牌刷新
                if (retry_count == 0 and retry_on_oauth_failure and
                        self._handle_oauth2_token_refresh(response, request_kwargs)):
                    retry_count += 1
                    logger.info(f"令牌刷新成功，重试请求 ({retry_count}/{max_retries})")
                    continue

                # 执行响应钩子
                self._run_response_hooks(response)

                return response

            except requests.exceptions.Timeout as e:
                elapsed = time.time() - start_time
                logger.error(f"请求超时: {url}, 耗时: {elapsed:.2f}s")
                raise
            except requests.exceptions.ConnectionError as e:
                elapsed = time.time() - start_time
                logger.error(f"连接错误: {url}, 耗时: {elapsed:.2f}s, 错误: {e}")
                raise
            except requests.exceptions.RequestException as e:
                elapsed = time.time() - start_time
                logger.error(f"请求异常: {url}, 耗时: {elapsed:.2f}s, 错误: {e}")
                raise
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"未知错误: {url}, 耗时: {elapsed:.2f}s, 错误: {e}")
                raise

        # 如果重试后仍然失败，返回最后一次响应
        return response

    def get_oauth2_token_info(self) -> Dict:
        """获取OAuth 2.0令牌信息"""
        if not self.use_oauth2 or not self.oauth_client:
            return {}

        token_info = {}
        if hasattr(self.oauth_client, '_token') and self.oauth_client._token:
            token = self.oauth_client._token
            token_info = {
                'access_token': token.access_token[:20] + '...' if token.access_token else None,
                'token_type': token.token_type,
                'expires_in': token.expires_in,
                'is_expired': token.is_expired,
                'expires_at': datetime.fromtimestamp(token.expires_at).strftime('%Y-%m-%d %H:%M:%S'),
                'scope': token.scope
            }

        return token_info

    def refresh_oauth2_token(self):
        """刷新OAuth 2.0令牌"""
        if self.use_oauth2 and self.oauth_client:
            self.oauth_client.refresh_token()

    def clear_oauth2_token(self):
        """清除OAuth 2.0令牌"""
        if self.use_oauth2 and self.oauth_client:
            self.oauth_client.clear_token()

    # 快捷方法
    def get(self, url: str, **kwargs) -> requests.Response:
        """发送GET请求"""
        return self.send_request('GET', url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """发送POST请求"""
        return self.send_request('POST', url, **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        """发送PUT请求"""
        return self.send_request('PUT', url, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        """发送DELETE请求"""
        return self.send_request('DELETE', url, **kwargs)

    def patch(self, url: str, **kwargs) -> requests.Response:
        """发送PATCH请求"""
        return self.send_request('PATCH', url, **kwargs)

    def head(self, url: str, **kwargs) -> requests.Response:
        """发送HEAD请求"""
        return self.send_request('HEAD', url, **kwargs)

    def options(self, url: str, **kwargs) -> requests.Response:
        """发送OPTIONS请求"""
        return self.send_request('OPTIONS', url, **kwargs)

    def add_header(self, key: str, value: str):
        """添加请求头"""
        self.session.headers[key] = value
        logger.debug(f"添加请求头: {key}: {value}")

    def remove_header(self, key: str):
        """移除请求头"""
        if key in self.session.headers:
            del self.session.headers[key]
            logger.debug(f"移除请求头: {key}")

    def clear_headers(self):
        """清空请求头"""
        self.session.headers.clear()
        self.session.headers.update(self.default_headers)
        logger.debug("清空请求头")

    def set_auth(self, auth_type: str, **kwargs):
        """设置认证"""
        if auth_type.lower() == 'oauth2':
            # 已经是默认认证方式
            pass
        elif auth_type.lower() == 'bearer':
            token = kwargs.get('token')
            if token:
                self.add_header('Authorization', f'Bearer {token}')
        elif auth_type.lower() == 'basic':
            username = kwargs.get('username')
            password = kwargs.get('password')
            if username and password:
                from requests.auth import HTTPBasicAuth
                self.session.auth = HTTPBasicAuth(username, password)
        elif auth_type.lower() == 'digest':
            username = kwargs.get('username')
            password = kwargs.get('password')
            if username and password:
                from requests.auth import HTTPDigestAuth
                self.session.auth = HTTPDigestAuth(username, password)
        elif auth_type.lower() == 'api_key':
            key = kwargs.get('key')
            value = kwargs.get('value')
            location = kwargs.get('location', 'header')
            if key and value:
                if location == 'header':
                    self.add_header(key, value)
                elif location == 'query':
                    # 需要在请求参数中添加
                    pass

        logger.debug(f"设置认证: {auth_type}")


# 创建全局请求客户端实例
request_client = RequestClient()


# 请求钩子示例
def log_request_details(request_kwargs: Dict):
    """记录请求详情钩子"""
    logger.debug(f"请求详情: {request_kwargs.get('method')} {request_kwargs.get('url')}")


def validate_response(response: requests.Response):
    """验证响应钩子"""
    if response.status_code >= 400:
        logger.warning(f"请求失败: {response.status_code} {response.reason}")


# 添加默认钩子
request_client.add_request_hook(log_request_details)
request_client.add_response_hook(validate_response)
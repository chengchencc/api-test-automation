from src.config.settings import project_config

if __name__ == "__main__":
    from src.common.request_client import request_client
    request_client.set_auth("Bearer", **{"token": project_config.TEST_AUTH_TOKEN})
    response = request_client.send_request(method="GET",url="/api-feedback/Process/queryDoneTaskByPage?column=createTime&order=desc&pageNo=1&pageSize=10")
    print(response)
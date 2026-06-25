from docker import DockerClient


def get_client() -> DockerClient:
    return DockerClient.from_env()

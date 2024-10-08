from pydantic import BaseModel


class UserInDB(BaseModel):
    username: str
    hashed_password: str


# in-memory users
mock_users = {
    "admin": {
        "username": "aasim",
        "hashed_password": "$2b$12$ZZdwqmyxe/6Rtd8kp2Ahxue2p6UHDnHFEhJw4vTiUdR93cx3.7X4S"  # hashed "123"
    },
    "aasim": {
        "username": "khan",
        "hashed_password": "$2b$12$ZZdwqmyxe/6Rtd8kp2Ahxue2p6UHDnHFEhJw4vTiUdR93cx3.7X4S"  # hashed "123"
    }
}

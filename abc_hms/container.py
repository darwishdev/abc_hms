
# abc_hms/container.py
from .pos.usecase.auth_usecase import AuthUsecase
from .pos.repo.auth_repo import AuthRepo

class AppContainer:
    def __init__(self):
        self.auth_repo = AuthRepo()
        self.auth_usecase = AuthUsecase(self.auth_repo)



# global singleton container for APIs
container = AppContainer()

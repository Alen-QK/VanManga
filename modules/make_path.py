import os


def path_exists_make(path):
    # path: 需要判断的路径

    if os.path.exists(path):
        pass
    else:
        os.makedirs(path, exist_ok= True)
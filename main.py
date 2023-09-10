# Copyright (c) 2023 Szymon Kasprzycki
# This file is protected by MIT license. See LICENSE for more information.

from app import App
import threading

if __name__ == '__main__':
    app = App()
    thread = threading.Thread(target=app.run)
    second_thread = threading.Thread(target=app.run_automatic_update)
    thread.start()
    second_thread.start()

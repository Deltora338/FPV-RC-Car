import time


def run(a, b):
    print(a, b)

if __name__ == "__main__":
    time_ = time.time()
    try:
        with open("camera_allowance_variable.txt", "x") as file:
            file.write("300")
        camera = 300
    except Exception as e:
        with open("camera_allowance_variable.txt", 'r') as file:
            camera = file.read()
    run(time_, camera)

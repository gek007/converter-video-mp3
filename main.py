import json


def main():
    print("Hello from system-design!")

    # data = [
    #     {
    #         "id": 1,
    #         "video_fid": "123",
    #         "username": "john",
    #         "mp3_fid": "456",
    #         "status": "processing",
    #     },
    #     {
    #         "id": 2,
    #         "video_fid": "456",
    #         "username": "jane",
    #         "mp3_fid": "789",
    #         "status": "completed",
    #     },
    # ]

    # with open("data.json", "w") as f:
    #     json.dump(data, f, indent=4)

    with open("data.json", "r") as f:
        data = json.load(f)
        print(data)


if __name__ == "__main__":
    main()

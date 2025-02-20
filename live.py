import cv2
import numpy as np


def listAvailableCameras(max_cameras=10):
    available_cameras = []
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras


def selectCamera():
    cameras = listAvailableCameras()
    if not cameras:
        print("Нет доступных камер")
        exit(0)
    
    print("Доступные камеры:")
    for index in cameras:
        print(f"[{index}] Камера {index}")
    
    while True:
        try:
            selected_index = int(input("Выберите номер камеры: "))
            if selected_index in cameras:
                return selected_index
            else:
                print("Неверный выбор. Попробуйте снова")
        except ValueError:
            print("Введите номер камеры")


def processFrame(frame: np.ndarray) -> np.ndarray:
    if frame.shape[1] < 1280:
        print(f"Warning: Frame width is less than 1280. Current width: {frame.shape[1]}")
        return frame
    
    left_lo = frame[:, :640, 1].astype(np.uint16)
    right_hi = frame[:, 640:, 1].astype(np.uint16)

    combined_16 = (right_hi << 8) | left_lo

    combined_8 = (combined_16 >> 8).astype(np.uint8)

    inverted = 255 - combined_8

    out = cv2.cvtColor(inverted, cv2.COLOR_GRAY2BGR)
    return out


def main():
    camera_index = selectCamera()
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print("Ошибка: не удалось открыть камеру")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    print("Нажмите 'q' для выхода.")
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("Ошибка: не удалось получить кадр.")
            break
        
        processed_frame = processFrame(frame)
        
        cv2.imshow('original', frame)
        cv2.imshow('processed', processed_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
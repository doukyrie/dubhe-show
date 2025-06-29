import cv2

# 图像路径（可以是相对路径或绝对路径）
image_path = 'armored_vehicle-1.png'

# 使用 OpenCV 读取图像
image = cv2.imread(image_path)

# 检查是否成功读取
if image is None:
    print("无法加载图像，请检查路径是否正确")
else:
    print("图像加载成功！")
    
    # 显示图像（可选）
    cv2.imshow('Image', image)
    cv2.waitKey(0)            # 等待按键
    cv2.destroyAllWindows()   # 关闭所有窗口
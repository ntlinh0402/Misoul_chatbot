# process_pdfs.py
import os
import sys
from app.pdf_processor_langchain import PDFProcessor

def main():
    # Hiển thị banner
    print("=" * 40)
    print("MISOUL PDF Processor")
    print("=" * 40)
    
    # Kiểm tra thư mục data/pdfs
    pdfs_directory = os.path.join('data', 'pdfs')
    if not os.path.exists(pdfs_directory):
        os.makedirs(pdfs_directory)
        print(f"✅ Đã tạo thư mục PDF: {pdfs_directory}")
    
    # Đếm số lượng PDF hiện có
    pdf_files = [f for f in os.listdir(pdfs_directory) if f.lower().endswith('.pdf')]
    print(f"Số lượng file PDF hiện có: {len(pdf_files)}")
    
    # Hướng dẫn người dùng
    print("\nHướng dẫn:")
    print("1. Đặt các file PDF vào thư mục data/pdfs")
    print("2. Đặt tên file PDF theo cấu trúc: [tên]_[danh_mục].pdf")
    print("   Các danh mục: anxiety, depression, cbt_techniques, mindfulness, crisis")
    print("   Ví dụ: kythuat_thaythe_mindfulness.pdf")
    print("")
    
    if len(pdf_files) == 0:
        print("⚠️ Không có file PDF trong thư mục. Hãy thêm file PDF và chạy lại script này.")
        return
    
    # Hỏi người dùng muốn tiếp tục không
    while True:
        answer = input("Bạn muốn xử lý các file PDF này? (y/n): ")
        if answer.lower() in ['y', 'yes']:
            break
        elif answer.lower() in ['n', 'no']:
            print("Hủy bỏ. Hãy đặt file PDF vào thư mục data/pdfs và chạy lại script này.")
            return
    
    # Khởi tạo processor và xử lý PDF
    processor = PDFProcessor()
    print("\nBắt đầu xử lý PDF...")
    success = processor.process_all_pdfs()
    
    if success:
        print("\n✅ Hoàn tất xử lý PDF!")
        print("Bạn có thể chạy 'python run.py' để khởi động MISOUL API")
    else:
        print("\n❌ Có lỗi khi xử lý PDF. Hãy kiểm tra lại các file PDF và thử lại.")

if __name__ == "__main__":
    main()
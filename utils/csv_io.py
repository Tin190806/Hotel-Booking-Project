import csv 
from pathlib import Path
from typing import List,Dict
"""
Module tiện ích xử lý đọc và ghi file CSV.
Được sử dụng bởi tầng Service để thao tác lưu trữ dữ liệu.
Không chứa nghiệp vụ.
"""

def read_csv(path: Path) -> List[Dict]:
    """
    Đọc dữ liệu từ file CSV và trả về danh sách dict.

    Mỗi dòng trong file CSV tương ứng với một dict,
    trong đó key là tên cột và value là dữ liệu của dòng đó.

    Nếu file không tồn tại, trả về danh sách rỗng.
    """
    if not path.exists():
        return []
    
    with path.open("r",encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)
    
def write_csv(path: Path,rows: List[Dict],fieldnames: List[str]) -> None:
    """
    Ghi danh sách dict xuống file CSV.

    - Tự động tạo thư mục nếu chưa tồn tại
    - Ghi header dựa trên fieldnames
    - Ghi toàn bộ dữ liệu mới (ghi đè)
    """
    path.parent.mkdir(parents = True,exist_ok= True)

    with path.open("w",encoding="utf-8") as f:
        writer = csv.DictWriter(f,fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
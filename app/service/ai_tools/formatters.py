from typing import Dict, Any, Optional

def _format_tim_phong_trong(args: Dict[str, Any], result: Dict[str, Any]) -> str:
    status = result.get("status")
    if status != "success":
        return result.get("message", "Không tìm thấy phòng trống phù hợp.")

    rooms = result.get("danh_sach_phong", [])
    ngay = result.get("ngay")
    ca = result.get("ca")
    tong_so = result.get("tong_so_phong_trong", len(rooms))

    time_desc = f"vào ngày **{ngay}**" + (f", **Ca {ca}**" if ca else "")
    lines = [f"🏫 **Tìm thấy {tong_so} phòng trống phù hợp {time_desc}:**\n"]

    for r in rooms:
        lines.append(
            f"- **Phòng {r['ma_phong']}** ({r.get('loai_phong', 'Phòng học')}) | "
            f"Vị trí: Tòa {r.get('toa', '')} Tầng {r.get('tang', '')} | "
            f"Sức chứa: {r.get('suc_chua', 0)} chỗ"
        )

    if rooms:
        first_room = rooms[0]["ma_phong"]
        suggested_ca = ca if ca else 1
        lines.append(f"\n💡 *Gợi ý: Bạn có thể nhắn **'Mượn phòng {first_room} ca {suggested_ca}'** để tiến hành đăng ký.*")

    return "\n".join(lines)


def _format_tra_cuu_lich_phong(args: Dict[str, Any], result: Dict[str, Any]) -> str:
    status = result.get("status")
    if status != "success":
        return result.get("message", "Không tìm thấy lịch học cho phòng này.")

    ma_phong = result.get("ma_phong", args.get("ma_phong", ""))
    loai_phong = result.get("loai_phong", "")
    schedules = result.get("danh_sach_lich", [])

    lines = [f"📅 **Lịch hoạt động của phòng {ma_phong}** ({loai_phong}):\n"]
    for s in schedules:
        lines.append(
            f"- **Ngày {s.get('ngay')} (Ca {s.get('ca')})**: {s.get('noi_dung', 'Lịch học')} "
            f"[{s.get('loai', 'Chính khóa')}] - {s.get('so_nguoi', 0)} người"
        )

    return "\n".join(lines)


def _format_kiem_tra_lang_phi_dien(args: Dict[str, Any], result: Dict[str, Any]) -> str:
    status = result.get("status")
    if status != "success":
        return result.get("message", "Chưa có dữ liệu phân tích lãng phí điện.")

    ngay = result.get("ngay", args.get("ngay", "hôm nay"))
    tong_so = result.get("tong_so_phong_lang_phi", 0)
    warnings = result.get("danh_sach_canh_bao", [])

    if tong_so == 0:
        return f"✅ **Hệ thống đã kiểm tra ngày {ngay}:** Hiện không có phòng học nào có dấu hiệu lãng phí điện năng."

    lines = [f"⚡ **Cảnh báo: Phát hiện {tong_so} phòng có dấu hiệu lãng phí điện năng (Ngày {ngay}):**\n"]
    for w in warnings:
        lines.append(
            f"- **Phòng {w.get('ma_phong')} (Ca {w.get('ca')})**: Tiêu thụ **{w.get('dien_tieu_thu', 0):,.1f} kWh** "
            f"nhưng không có lịch học. Chi phí lãng phí ước tính: **{w.get('chi_phi_uoc_tinh', 0):,.0f} VNĐ**."
        )

    lines.append("\n💡 *Gợi ý: Bộ phận quản lý tòa nhà nên cử nhân sự kiểm tra và tắt thiết bị tại các phòng trên để tiết kiệm điện.*")
    return "\n".join(lines)


def _format_tra_cuu_tong_quan_dien(args: Dict[str, Any], result: Dict[str, Any]) -> str:
    status = result.get("status")
    if status != "success":
        return result.get("message", "Chưa có dữ liệu tổng hợp điện năng.")

    lines = [
        "📊 **Thống kê điện năng tiêu thụ toàn trường:**\n",
        f"- **Tổng điện năng ghi nhận**: **{result.get('tong_kwh', 0):,.1f} kWh**",
        f"- **Mức tiêu thụ trung bình mỗi phòng**: **{result.get('trung_binh_kwh_moi_phong', 0):,.1f} kWh**",
        f"- **Tổng số lượt đo cảm biến**: {result.get('so_ban_ghi', 0)} lượt"
    ]
    return "\n".join(lines)


def _format_tra_cuu_thiet_bi_hong(args: Dict[str, Any], result: Dict[str, Any]) -> str:
    status = result.get("status")
    if status != "success":
        return result.get("message", "Hiện tại không có thiết bị nào báo hỏng.")

    tickets = result.get("danh_sach_hong", [])
    tong_so = result.get("tong_so_su_co", len(tickets))

    lines = [f"🔧 **Danh sách sự cố & thiết bị đang báo hỏng ({tong_so} phiếu đang xử lý):**\n"]
    for t in tickets:
        tb_info = f" (TB #{t['ma_tb']})" if t.get("ma_tb") else ""
        lines.append(
            f"- **Phiếu #{t.get('ma_phieu')} - Phòng {t.get('ma_phong')}**{tb_info}: "
            f"{t.get('mo_ta')} | Trạng thái: **{t.get('trang_thai')}**"
        )

    return "\n".join(lines)


def _format_tao_phieu_bao_hong(args: Dict[str, Any], result: Dict[str, Any]) -> str:
    status = result.get("status")
    msg = result.get("message", "")
    if status == "success":
        ma_phieu = result.get("ma_phieu")
        return f"✅ **{msg}**\n\n📌 *Mã phiếu: **#{ma_phieu}**. Đội kỹ thuật Smart Campus sẽ tiếp nhận và xử lý sự cố sớm nhất.*"
    return f"⚠️ **Không thể tạo phiếu:** {msg}"


def _format_kiem_tra_kha_dung_dat_phong(args: Dict[str, Any], result: Dict[str, Any]) -> str:
    kha_dung = result.get("kha_dung", False)
    msg = result.get("message", "")
    if kha_dung:
        ma_phong = result.get("ma_phong", "")
        ca = result.get("ca", 1)
        return (
            f"✅ **{msg}**\n\n"
            f"💡 *Gợi ý: Nếu bạn muốn gửi đơn mượn phòng này, hãy bảo tôi: **'Mượn phòng {ma_phong} ca {ca} vì [lý do của bạn]'**.*"
        )
    return f"⚠️ **{msg}**"


def _format_tao_yeu_cau_muon_phong(args: Dict[str, Any], result: Dict[str, Any]) -> str:
    status = result.get("status")
    msg = result.get("message", "")
    if status == "success":
        ma_yc = result.get("ma_yc")
        return (
            f"🎉 **{msg}**\n\n"
            f"📋 *Mã đơn mượn: **#{ma_yc}**. Đơn đăng ký đã được chuyển tới Ban Quản trị để duyệt.*"
        )
    return f"⚠️ **{msg}**"


FORMATTER_REGISTRY = {
    "tim_phong_trong": _format_tim_phong_trong,
    "tra_cuu_lich_phong": _format_tra_cuu_lich_phong,
    "kiem_tra_lang_phi_dien": _format_kiem_tra_lang_phi_dien,
    "tra_cuu_tong_quan_dien": _format_tra_cuu_tong_quan_dien,
    "tra_cuu_thiet_bi_hong": _format_tra_cuu_thiet_bi_hong,
    "tao_phieu_bao_hong": _format_tao_phieu_bao_hong,
    "kiem_tra_kha_dung_dat_phong": _format_kiem_tra_kha_dung_dat_phong,
    "tao_yeu_cau_muon_phong": _format_tao_yeu_cau_muon_phong,
}

def format_tool_response(tool_name: str, tool_args: Dict[str, Any], tool_result: Dict[str, Any]) -> str:
    """
    Chuyển đổi kết quả thực thi Tool thành Markdown câu trả lời hoàn chỉnh,
    thân thiện, chuyên nghiệp mà KHÔNG cần gọi thêm lượt thứ 2 tới LLM.
    """
    formatter = FORMATTER_REGISTRY.get(tool_name)
    if formatter:
        try:
            return formatter(tool_args, tool_result)
        except Exception:
            pass

    return tool_result.get("message", "Đã thực hiện xong yêu cầu.")

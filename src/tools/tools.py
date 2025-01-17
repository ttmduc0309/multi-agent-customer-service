from autogen_core.components.tools import FunctionTool
from ..messages import *


def execute_order(product: str, price: int) -> str:
    print("\n\n=== Order Summary ===")
    print(f"Product: {product}")
    print(f"Price: ${price}")
    print("=================\n")
    confirm = input("Confirm order? y/n: ").strip().lower()
    if confirm == "y":
        print("Order execution successful!")
        return "Success"
    else:
        print("Order cancelled!")
        return "User cancelled order."


def look_up_item(search_query: str) -> str:
    item_id = "item_132612938"
    print("Found item:", item_id)
    return item_id


def execute_refund(item_id: str, reason: str = "not provided") -> str:
    print("\n\n=== Refund Summary ===")
    print(f"Item ID: {item_id}")
    print(f"Reason: {reason}")
    print("=================\n")
    print("Refund execution successful!")
    return "success"

def save_login_fail_checking(nickName: str, portalGame: str) -> str:
    return f"""Lưu thông tin thành công: 
            - nick name:{nickName} 
            - cong game:{portalGame}
            - record_id: 123456"""

def update_login_fail_checking(record_id: str, nickName: str | None, portalGame: str | None) -> str:
    return f"""Cập nhật thông tin thành công: 
            - nick name:{nickName} 
            - cong game:{portalGame}"""

def save_forget_acc_checking(nickName: str, portalGame: str) -> str:
    return f"""Lưu thông tin thành công: 
            - nick name:{nickName} 
            - cong game:{portalGame}
            - record_id: 123456"""

def update_forget_acc_checking(record_id: str, nickName: str | None, portalGame: str | None) -> str:
    return f"""Cập nhật thông tin thành công: 
            - nick name:{nickName} 
            - cong game:{portalGame}"""

save_login_fail_tool = FunctionTool(save_login_fail_checking, description="Save login fail checking")
update_login_fail_tool = FunctionTool(update_login_fail_checking, description="Update login fail checking")
save_forget_acc_tool = FunctionTool(save_forget_acc_checking, description="Save forget acc checking")
update_forget_acc_tool = FunctionTool(update_forget_acc_checking, description="Update forget acc checking")

execute_order_tool = FunctionTool(execute_order, description="Price should be in USD.")
look_up_item_tool = FunctionTool(
    look_up_item, description="Use to find item ID.\nSearch query can be a description or keywords."
)
execute_refund_tool = FunctionTool(execute_refund, description="")
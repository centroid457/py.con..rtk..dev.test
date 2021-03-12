# todo: tests

import sys
import socket
import re
import contracts
import pathlib
import requests

# [+]------------------------------------------------------
# 0=INITIAL DATA
models_used_list = ["TD-1", ]
dev_found_mac_dict = {}
path_to_save_results = pathlib.Path.cwd() / "RESULTS"   # will change from script argv!

# [+]------------------------------------------------------
# 1=PATH TO SAVE
if len(sys.argv) == 3:
    argv_name = sys.argv[1]
    argv_value = sys.argv[2]
    if argv_name == "--dir":
        try:
            path_to_save_results = pathlib.Path.cwd() / argv_value
        except:
            pass
    print(sys.argv)
path_to_save_results.mkdir(exist_ok=True)


# [+?]-----------------------------------------------------
# 2=DEV TEST=json_rpc
@contracts.contract(ip=str, dev_id=int, returns="int|None")
def dev_test_start(ip, dev_id):
    dev_url = f"http://{ip}/api"
    request_json_rpc = {"jsonrpc": "2.0", "method": "do_test", "id": dev_id}
    try:
        response_http = requests.post(url=dev_url, json=request_json_rpc)
    except:
        return None

    try:
        # response_http_json = response_http.json()                             #del by corrector
        # response_json_rpc = response_http_json.get("data", {"result": -1})    #del by corrector
        response_json_rpc = response_http.json()        # add by corrector

        if response_json_rpc["jsonrpc"] == "2.0" and response_json_rpc["id"] == dev_id:
            response_dev_result = response_json_rpc["result"]
            return response_dev_result
    except:
        return -1


# [+]------------------------------------------------------
# 3=SAVE RESULT
@contracts.contract(mac=str)
def dev_test_save_result(mac):
    dev_dict = dev_found_mac_dict[mac]

    dev_test_result = dev_dict.get("result", None)
    if dev_test_result == 0:
        file_dev_test_result = "пройден успешно!"
    elif type(dev_test_result) == int and 0 < dev_test_result <= 100:
        file_dev_test_result = f"провален: ошибка {dev_test_result}."
    elif dev_test_result is None:
        file_dev_test_result = f"провален: НЕТ ОТВЕТА."
    else:
        file_dev_test_result = "провален: некорректный ответ."

    file_dev_data = f"Тест {dev_dict['model']} с SN {dev_dict.get('sn', 'ERROR')} {file_dev_test_result}"
    with open(file=path_to_save_results / f"{dev_dict.get('sn', mac)}.txt", mode="w", encoding="utf-8") as file_obj:
        file_obj.write(file_dev_data)
    return


# [+]------------------------------------------------------
# 4=UDP LISTEN
def udp_listen():
    json_rpc_dev_id = 0

    udp_multicast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_multicast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_multicast.bind(('', 12345))

    while True:
        udp_get_msg_b, (dev_ip, _) = udp_multicast.recvfrom(1024)
        udp_get_msg = udp_get_msg_b.decode("utf-8")
        # print(udp_get_msg)

        mask_udp = r"(.+),([0-9a-fA-F]{2}(?:[:-][0-9a-fA-F]{2}){5}),(\d{0,7})"
        match = re.fullmatch(mask_udp, udp_get_msg)
        if match:
            json_rpc_dev_id += 1

            dev_model = match[1]
            dev_mac = match[2]
            dev_sn = match[3]

            if dev_model in models_used_list:
                print("Get UDP: ", dev_ip, dev_mac, dev_sn)

                if dev_mac not in dev_found_mac_dict:
                    if dev_ip is None:
                        continue

                    dev_found_mac_dict.update({dev_mac: {"model": dev_model, "sn": dev_sn, "ip": dev_ip}})
                    dev_test_result = dev_test_start(dev_ip, json_rpc_dev_id)
                    dev_found_mac_dict[dev_mac].update({"result": dev_test_result})

                    dev_test_save_result(dev_mac)


udp_listen()

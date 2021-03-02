# todo: tests

import sys
import socket
import struct
import re
import contracts
import subprocess
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


# [+WIN/?Lin]------------------------------------------------------
# 2=GET IP = DONT NEED
"""
@contracts.contract(mac=str, returns="None|str")
def dev_get_ip_from_mac(mac):
    arp_sp = subprocess.Popen(f"arp -a", text=True, shell=True, stdout=subprocess.PIPE)
    arp_readlines = arp_sp.stdout.readlines()

    for line in arp_readlines:
        if mac in line:
            ip = line.split()[0]
            print(ip)
            return ip
    return None
"""

# [+?]-----------------------------------------------------
# 3=DEV TEST=json_rpc
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
        response_json_rpc = response_http.json()        #add by corrector

        if response_json_rpc["jsonrpc"] == "2.0" and response_json_rpc["id"] == dev_id:
            response_dev_result = response_json_rpc["result"]
            return response_dev_result
    except:
        return -1


# [+]------------------------------------------------------
# 4=SAVE RESULT
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
# 5=UDP LISTEN
def udp_listen():
    json_rpc_dev_id = 0

    udp_multicast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_multicast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_multicast.bind(('', 12345))
    mreq = struct.pack("=4sl", socket.inet_aton("225.1.1.1"), socket.INADDR_ANY)
    udp_multicast.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        # udp_get_msg_b = udp_multicast.recv(10240)     #del by corrector
        udp_get_msg_b, (dev_ip, _) = udp_multicast.recvfrom(10240)  #add by corrector
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
                print("found: ", dev_mac, dev_sn)

                if dev_mac not in dev_found_mac_dict:
                    #dev_ip = dev_get_ip_from_mac(dev_mac)  #del by corrector
                    if dev_ip is None:
                        continue

                    dev_found_mac_dict.update({dev_mac: {"model": dev_model, "sn": dev_sn, "ip": dev_ip}})
                    dev_test_result = dev_test_start(dev_ip, json_rpc_dev_id)
                    dev_found_mac_dict[dev_mac].update({"result": dev_test_result})

                    dev_test_save_result(dev_mac)


if __name__ == '__main__':
    udp_listen()

sys.exit()

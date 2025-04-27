# _*_ coding=utf-8 _*_

if __name__ == '__main__':
    import ipaddress
    import subprocess
    import datetime
    import sys
    from concurrent.futures import ThreadPoolExecutor, as_completed


    def ping(ip, timeout, count, successful_ips, failed_ips):
        """
        对单个 IP 执行 ping 测试
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cmd = ['ping', '-c', str(count), '-W', str(timeout), str(ip)]

        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            ip_str = str(ip).ljust(15)  # 对齐 IP 地址，便于阅读

            if result.returncode == 0:
                print(f"[{timestamp}] {ip_str} 可达(当前尝试发送了 {count} 个报文)")
                successful_ips.append(ipaddress.IPv4Address(ip))
                return True
            else:
                print(f"[{timestamp}] {ip_str} 不可达(当前尝试发送了 {count} 个报文)")
                failed_ips.append(ipaddress.IPv4Address(ip))
                return False

        except Exception as e:
            print(f"[{timestamp}] {ip_str} 测试出错: {str(e)}")
            failed_ips.append(ipaddress.IPv4Address(ip))
            return False


    def test_ip_list(ip_list, timeout, count, max_workers, successful_ips, failed_ips):
        """
        并发测试 IP 列表
        """
        total_ips = len(ip_list)
        completed = 0

        print(f"\n开始测试 {total_ips} 个IP地址...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(ping, ip, timeout, count, successful_ips, failed_ips): ip for ip in ip_list}
            for future in as_completed(futures):
                completed += 1
                if completed % 10 == 0:  # 每完成10个IP打印一次进度
                    print(f"进度: {completed}/{total_ips} ({(completed / total_ips * 100):.1f}%)")
                future.result()

        print(f"IP测试完成: {completed}/{total_ips}\n")


    def test_ip_range(start_ip, end_ip, timeout, count, max_workers, successful_ips, failed_ips):
        """
        测试 IP 范围
        """
        try:
            start = ipaddress.IPv4Address(start_ip)
            end = ipaddress.IPv4Address(end_ip)
            ip_list = [str(ipaddress.IPv4Address(ip)) for ip in range(int(start), int(end) + 1)]

            test_ip_list(ip_list, timeout, count, max_workers, successful_ips, failed_ips)

        except Exception as e:
            print(f"IP 范围格式错误: {str(e)}")
            sys.exit(1)


    def test_ip_subnet(subnet, timeout, count, max_workers, successful_ips, failed_ips):
        """
        测试 IP 子网
        """
        try:
            network = ipaddress.IPv4Network(subnet, strict=False)
            ip_list = [str(ip) for ip in network.hosts()]

            test_ip_list(ip_list, timeout, count, max_workers, successful_ips, failed_ips)

        except Exception as e:
            print(f"子网格式错误: {str(e)}")
            sys.exit(1)


    def print_summary(successful_ips, failed_ips, output_file=None):
        """
        打印测试结果汇总并保存到文件
        """
        summary = []
        summary.append("\n测试结果汇总:")
        total = len(successful_ips) + len(failed_ips)
        summary.append(f"总计测试 IP 数: {total}")
        summary.append(f"可达 IP 数: {len(successful_ips)}")
        summary.append(f"不可达 IP 数: {len(failed_ips)}")

        if successful_ips:
            summary.append("\n可达 IP 列表:")
            for ip in sorted(successful_ips):
                summary.append(str(ip))

        if failed_ips:
            summary.append("\n不可达 IP 列表:")
            for ip in sorted(failed_ips):
                summary.append(str(ip))

        # 打印到控制台
        print('\n'.join(summary))

        # 保存到文件
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(summary))
            print(f"\n结果已保存到文件: {output_file}")


    def read_ips_from_file(filename, successful_ips, failed_ips, timeout, count, max_workers):
        """
        从文件中读取IP地址列表进行测试
        """
        try:
            with open(filename, 'r') as f:
                ip_list = [line.strip() for line in f if line.strip()]
            if not ip_list:
                print("文件为空或格式不正确")
                sys.exit(1)
            test_ip_list(ip_list, timeout, count, max_workers, successful_ips, failed_ips)
        except FileNotFoundError:
            print(f"未找到文件: {filename}")
            sys.exit(1)
        except Exception as e:
            print(f"读取文件出错: {str(e)}")
            sys.exit(1)


    def main():
        timeout = 2
        count = 2
        max_workers = 10
        successful_ips = []
        failed_ips = []

        print("\n请选择测试模式：")
        print("1. 测试单个IP")
        print("2. 测试IP范围")
        print("3. 测试子网")
        print("4. 从ip.txt文件读取IP列表")

        choice = input("\n请输入选择（1-4）: ").strip()

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        output_file = f"ping_results_{timestamp}.txt"

        if choice == "1":
            ip = input("请输入要测试的IP地址: ").strip()
            ping(ip, timeout, count, successful_ips, failed_ips)
        elif choice == "2":
            ip_range = input("请输入IP范围（格式：start_ip-end_ip）: ").strip()
            try:
                start_ip, end_ip = ip_range.split('-')
                test_ip_range(start_ip.strip(), end_ip.strip(), timeout, count, max_workers, successful_ips, failed_ips)
            except ValueError:
                print("IP范围格式错误，正确格式为: start_ip-end_ip")
                sys.exit(1)
        elif choice == "3":
            subnet = input("请输入子网（格式：x.x.x.x/xx）: ").strip()
            test_ip_subnet(subnet, timeout, count, max_workers, successful_ips, failed_ips)
        elif choice == "4":
            print("\n注意：请确保ip.txt文件存在，且每行包含一个有效的IP地址")
            read_ips_from_file('ip.txt', successful_ips, failed_ips, timeout, count, max_workers)
        else:
            print("无效的选择")
            sys.exit(1)

        print_summary(successful_ips, failed_ips, output_file)


    if __name__ == "__main__":
        main()
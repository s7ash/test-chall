import socket
import sys
import ssl
import re

def setConnectionParam(url):

    # Парсим URL, инициализируем HOST, PATH и PORT

    PORT = 80
    url = re.search("(.*\/\/)?([\da-z\.-]+)(\/[\W\w\.-\/]*)?", url)
    if not url:
        print("Wrong URL.")
        return 0
    if url.group(1) != None:
        if "http://" in url.group(1):
            PORT = 80
        elif "https://" in url.group(1):
            PORT = 443
        else:
            print("Wrong protocol.")
            return 0

    HOST = url.group(2)
    PATH = url.group(3) if url.group(3) else "/"

    return (HOST, PATH, PORT)

def treatmentHeaders(host, path, port):

    # Если в заголовке ответа есть поле Location, то получаем из его значения новые
    # HOST, PATH и PORT и заново создаем сокет.
    # Если ответ с кодом 200 - все OK, передаем HOST, PATH и PORT основной программе
    # Если что то другое - exit()

    while True:
        sock = None

        if port == 443:
            sock = ssl.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        sock.connect((host, port))
        sock.send(
                    "GET {path} HTTP/1.1\r\n" # Не HEAD, так как не все серверы понимают
                    "Host: {host}\r\n"
                    #"User-Agent: Mozilla/5.0(X11; Ubuntu; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0"
                    "Connection: close\r\n\r\n".format(host = host, path = path).encode("ascii")
            )

        header = sock.recv(1024).decode("utf-8", "ignore")

        if "200 OK" in header:
            sock.close()
            return (host, path, port)
        elif "Location:" in header:
            url = re.search("Location: (.*)\r\n", header).group(1)
            ret = setConnectionParam(url)
            
            sock.close()
            
            if ret == 0:
                return 0
            
            host, path, port = ret
            continue
        else:
            print("Unknown error:")
            print(header[:header.index('\r\n\r\n') + 4])
            sock.close()
            return 0

def main():

    if len(sys.argv) != 3:
        print("Wrong arguments.")
        sys.exit(0)

    ret = setConnectionParam(sys.argv[1])
    if ret == 0:
        sys.exit()

    HOST, PATH, PORT = ret

    fileName = sys.argv[2]

    ret = treatmentHeaders(HOST, PATH, PORT)
    if ret == 0:
        sys.exit()

    HOST, PATH, PORT = ret

    sock = None

    if PORT == 443:
        sock = ssl.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.connect((HOST, PORT))
    sock.send(
                "GET {path} HTTP/1.1\r\n"
                "Host: {host}\r\n"
                #"User-Agent: Mozilla/5.0(X11; Ubuntu; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0"
                "Connection: close\r\n\r\n".format(host = HOST, path = PATH).encode("ascii")
        )

    with open(fileName, "w") as file:
        result = sock.recv(4096).decode("utf-8", "ignore")
        result = result[result.index('\r\n\r\n') + 4:]
        while result and '</html>' not in result: # '</html> not in result - так как при HTTPS происходит timeout sock.recv(4096)'
            file.write(result)
            result = sock.recv(4096).decode("utf-8", "ignore")
        file.write(result)

    sock.close()

if __name__ == "__main__":
    main()
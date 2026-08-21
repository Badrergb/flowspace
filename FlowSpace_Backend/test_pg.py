import psycopg2
passwords = ['postgres', 'admin', 'password', 'root', '1234', '123456', '', 'flowspace', 'postgres123']
ports = [5432, 54322, 54321]
for port in ports:
    for p in passwords:
        try:
            conn = psycopg2.connect(f'postgresql://postgres:{p}@localhost:{port}/postgres')
            print(f"SUCCESS: postgresql://postgres:{p}@localhost:{port}/postgres")
        except Exception as e:
            pass
        try:
            conn = psycopg2.connect(f'postgresql://postgres:{p}@localhost:{port}/flowspace')
            print(f"SUCCESS: postgresql://postgres:{p}@localhost:{port}/flowspace")
        except Exception as e:
            pass

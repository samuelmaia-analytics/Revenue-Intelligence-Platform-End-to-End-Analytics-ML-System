$ErrorActionPreference = "Stop"

$mysqlAdmin = "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqladmin.exe"

& $mysqlAdmin --protocol=TCP -h localhost -P 3306 -u root --password=8kkBNe ping

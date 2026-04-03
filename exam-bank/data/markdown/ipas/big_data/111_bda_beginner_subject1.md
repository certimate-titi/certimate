## 1. 如附圖所示,使用Python 語言定義串列(list),下列敘述哪一項正確?
```python
a = [1, 2, 3]
b = [4, 5, 6, "HelloWorld"]
c = [a, b]
d = a + b
```
- (A) a[-1]的結果為[2, 3]
- (B) b[1:3]的結果為[5, 6]
- (C) c[1][2]的結果為5
- (D) d[1]的結果為7
**答案：B**

## 2. 關於R語言的資料型態,下列敘述哪一項錯誤?
- (A) R語言的基本資料單位稱作向量(vector)
- (B) 兩個維度的向量,稱為矩陣(matrix)
- (C) 多個維度的向量,稱為陣列(array)
- (D) 串列(list)只能是二維資料
**答案：D**

## 3. 如附圖所示,已知某企業自2020年第2季起最近5期的產品銷售量(單位為百萬元)為{50, 40, 60, 90, 70},以 R 語言建立 myts 時間序列物件(Time-series Objects),下列敘述哪一項正確?
```
> myts
     Qtr1 Qtr2 Qtr3 Qtr4
2020   50   40   60
2021   90   70
```
- (A) `myts <- ts(c(50,40,60,90,70))`
- (B) `myts <- ts(c(50,40,60,90,70), start = c(2020,2), frequency = 12)`
- (C) `myts <- ts(c(50,40,60,90,70), start = c(2020,2), frequency = 4)`
- (D) `myts <- ts(c(50,40,60,90,70), start = c(2020,2), frequency = 1)`
**答案：C**

## 4. 如附圖所示為R語言程式碼片段,下列敘述哪一項正確?
```
> mat_a <- matrix(c(1,2,3,4), ncol=2, byrow = TRUE)
> mat_b <- solve (mat_a)
> mat_b
     [,1] [,2]
[1,] -2.0  1.0
[2,]  1.5 -0.5
```
- (A) `mat_a[1,2]`結果為3
- (B) `class(mat_b)`結果為"list"
- (C) `byrow = TRUE` 表示物件是以橫列順序建立
- (D) `mat_a %*% mat_b`結果為0
**答案：C**

## 5. 如附圖所示為 Python 程式碼片段,下列敘述哪一項正確?
```python
1 city = ["台北市","台中市","新北市","高雄市","台北市"]
2 mycity1, mycity2, *mycity3 = city
```
- (A) `type(mycity1)`結果是 list
- (B) `mycity1`有3個元素
- (C) `mycity1 == mycity2` 結果為 True
- (D) `mycity3[2] == mycity1` 結果為 True
**答案：D**

## 6. 如附圖所示為R語言程式碼片段,下列敘述哪一項正確?
```
> mydata <- head(mtcars)
> mydata
                   mpg cyl disp  hp drat    wt  qsec vs am gear carb
Mazda RX4         21.0   6  160 110 3.90 2.620 16.46  0  1    4    4
Mazda RX4 Wag     21.0   6  160 110 3.90 2.875 17.02  0  1    4    4
Datsun 710        22.8   4  108  93 3.85 2.320 18.61  1  1    4    1
Hornet 4 Drive    21.4   6  258 110 3.08 3.215 19.44  1  0    3    1
Hornet Sportabout 18.7   8  360 175 3.15 3.440 17.02  0  0    3    2
Valiant           18.1   6  225 105 2.76 3.460 20.22  1  0    3    1
> mydata$cyl <- factor (mydata$cyl)
```
- (A) 資料物件 `mydata` 有12個變數(直行資料)
- (B) 執行 `length(levels(mydata$cyl))`的結果為6
- (C) 執行 `class(mydata$cyl)`的結果為"factor"
- (D) 執行 `mydata$cyl[6] <- 10` 的結果會將第6筆資料由原先6取代為10
**答案：C**

## 7. 如附圖所示為 Python 程式碼片段,其執行結果下列哪一項錯誤?
```python
d = {
    'key1': {1,2,3,4,5},
    'key2': {1,3,5,7,9}
}
```
- (A) 執行 `d['key3'] = 'Hello'`,可於`d`中新增鍵(key)為'key3'、值(value)為'Hello'
- (B) `d['key1']`的型態(type)為 set
- (C) `d['key1'][0]`的值1
- (D) 執行 `d['key1'].union(d['key2'])`之結果為{1, 2, 3, 4, 5, 7, 9}
**答案：C**

## 8. 如附圖所示為R語言程式碼片段,其執行結果下列哪一項錯誤?
```R
x <- 1:5
names(x) <- c("A", "B", "C", "D ", "E ")
print(x[-4])
```
- (A)
```
A
1
```
- (B)
```
A B C E
1 2 3 5
```
- (C)
```
D E
4 5
```
- (D)
```
B
2
```
**答案：B**

## 9. 將資料庫內的資料重複性,降低到最小的過程,下列哪一項正確?
- (A) 模組化
- (B) 階層化
- (C) 正規化
- (D) 結構化
**答案：C**

## 10. Microsoft SQL Server 是屬於下列哪一個類型的資料庫?
- (A) 階層式資料庫(Hierarchical Database)
- (B) 網狀式資料庫(Network Database)
- (C) 關聯式資料庫(Relational Database)
- (D) 物件導向式資料庫(Object-Oriented Database)
**答案：C**

## 11. 如附圖所示之程式碼為 Microsoft SQL Server 語法,其執行結果下列哪一項正確?
```sql
DECLARE @String varchar(25)
SET @String = '12,3,4'
SELECT CHARINDEX(',', @String)
```
- (A) 1
- (B) 2
- (C) 3
- (D) 4
**答案：B**

## 12. 關於 HBase,下列敘述哪一項錯誤?
- (A) HBase 進入 shell 的指令是「hbase shell」
- (B) HBase 建立 test 表格與 info 列簇的指令是「create 'test', 'info'」
- (C) HBase 表格中插入值的指令為 create
- (D) HBase 顯示所有表格指令為 list
**答案：C**

## 13. 關於 SQL 語法的使用,下列敘述哪一項錯誤?
- (A) SQL 查詢語法可由 `SELECT`、`FROM` 所組成,即使沒有 `WHERE` 也可以執行查詢動作
- (B) `WHERE` 為想查詢的資料條件
- (C) SQL 查詢語法中,`FROM`、`WHERE` 順序可以調整
- (D) 於 `SELECT` 後方加上*符號,表示查詢所有欄位的資料
**答案：C**

## 14. 如附圖所示,依照SQL 指令的正確使用順序,下列排序哪一項正確?
```
(1)SELECT
(2)GROUP BY
(3)HAVING
(4) FROM
```
- (A) (1)(2)(3)(4)
- (B) (1)(2)(4)(3)
- (C) (1)(4)(2)(3)
- (D) (1)(4)(3)(2)
**答案：C**

## 15. 主要應用在手機 App 的 ListView,最適合選用下列哪一種非關聯式資料庫(NoSQL)?
- (A) key-value 資料庫
- (B) memory-cache 資料庫
- (C) document 資料庫
- (D) graph 資料庫
**答案：C**

## 16. 關於關聯式資料庫(Relational database) 索引(Index)設計,下列敘述哪一項錯誤?
- (A) 索引欄位長度是越短越好
- (B) 使用 like 查詢索引欄位時,都可使用到索引效能
- (C) 將A、B、C欄位設定為複合索引時,僅搜尋A是不會用到索引的
- (D) 建立索引會占用儲存空間,資料增、刪、修時會異動儲存空間
**答案：B**

## 17. 如附圖所示,己知產品資料表:Product(產品編號,設計日期,設計者編號),建立 AFTER 觸發程序名稱為「產品刪除通知」,下列敘述(1)、(2)分別須填入哪二個指令?
```sql
CREATE TRIGGER (1)
ON Product
AFTER (2)
AS
PRINT "產品資料刪除通知"
GO
```
- (A) (1)產品資料刪除通知 (2)產品編號
- (B) (1)產品資料刪除通知 (2)DELETE
- (C) (1)DELETE (2)產品資料刪除通知
- (D) (1)DELETE (2)產品編號
**答案：B**

## 18. 關於一般關聯式資料庫管理系統(Relational Database Management Systems, RDBMS)中建立索引值(Index),下列敘述哪一項錯誤?
- (A) 於多欄上建立的索引不但不能加快查詢速度,反而會降低查詢速度
- (B) 字串類型的欄位也可以加入索引
- (C) 唯一索引(Unique Index)的值必須是唯一值
- (D) 不允許使用者從資料庫中快速擷取記錄
**答案：D**

## 19. 如附圖所示,R 語言使用 `read.table` 函數匯入 CSV 文字檔,執行 `df <- read.table("ipas.csv", sep = ",")`,下列敘述哪一項錯誤?
```
ipas.csv - 記事本
檔案(F) 編輯(E) 格式(O) 檢視(V) 說明
"Sepal.Length", "Sepal.Width","Petal.Length","Petal.Width","Species"
5.1,3.5,1.4,0.2,"setosa"
4.9,3,1.4,0.2,"setosa"
4.7,3.2,1.3,0.2,"setosa"
4.6,3.1,1.5,0.2,"setosa"
5,3.6,1.4,0.2,"setosa"
5.4,3.9,1.7,0.4,"setosa"
```
- (A) `class(df)`結果是"data.frame"
- (B) `nrow(df)`結果是 7
- (C) `ncol(df)`結果是5
- (D) `names(df)` 結果是"Sepal.Length" "Sepal.Width" "Petal.Length" "Petal.Width" "Species"
**答案：D**

## 20. 若要儲存結構性資料,下列哪一項為最合適的資料格式?
- (A) CSV
- (B) PDF
- (C) CSS
- (D) JPEG
**答案：A**

## 21. 下列敘述哪一項正確?
- (A) R 無法讀取聲音資料
- (B) R無法讀取 SAS 或 SPSS 格式資料
- (C) R無法讀取超過 1TB 的資料
- (D) R 可以讀取外部資料,包括統計軟體、試算表軟體、網路等等資料
**答案：D**

## 22. 關於R與Python 語言,下列敘述哪一項錯誤?
- (A) 在R語言中,可使用 `write.csv()`函數匯出.csv 檔
- (B) 在Python 語言中,可使用 `pandas` 的 `to_csv()`方法匯出.csv 檔
- (C) 在R語言中,無法使用`write.table()`函數匯出.csv 檔
- (D) 在Python 語言中,可使用 `open("file.csv", "w+")`讀寫.csv 檔
**答案：C**

## 23. 關於資料階層的範圍,下列哪一項錯誤?
- (A) 紀錄
- (B) 資料庫
- (C) 模型
- (D) 欄位
**答案：C**

## 24. 如附圖所示,已知某主機的日誌檔 ipas-tab.txt,各變數使用 Tab 鍵區隔,使用 Python 語言的 `pandas` 模組匯入日誌檔時,圖中的紅色框線空白處須加上下列哪一個參數?
```python
In: import pandas as pd
In: df = pd.read_csv("ipas-tab.txt", ______)
In: type(df)
Out: pandas.core.frame.DataFrame
```
- (A) `sep="\\Tab"`
- (B) `sep="\Tab"`
- (C) `sep="\t"`
- (D) `sep="\\t"`
**答案：C**

## 25. 如附圖所示,R語言使用 `read.fwf` 函數匯入固定寬度文字檔,圖中的紅色框線空白處須加上什麼參數?
```
ipas-width.txt - 記事本
檔案(F) 編輯(E) 格式(O) 檢視(V) 說明
1234 ipas
  56 bigdata
 789 analysis
```
```R
> read.fwf(file = "ipas-width.txt", ______)
>
  V1       V2
1 1234     ipas
2   56  bigdata
3  789 analysis
```
- (A) `width = c(5, 1, 8)`
- (B) `width = c(4, -1, 8)`
- (C) `width = c(5, -1, 8)`
- (D) `width = c(4, 1, 8)`
**答案：B**

## 26. 關於物件導向,下列敘述哪一項錯誤?
- (A) 一般而言物件導向設計使得程式碼提升再利用性且易讀性佳
- (B) 物件導向的函數有多形的(Polymorphic)特性,函數依據傳入的物件類別來進行相對應的運算,也可以在自訂函數中傳入不同的類別物件進行運算
- (C) 使用者應多關注程式語言環境中物件的類別特性,因為傳入物件的不同類別,運算之後會輸出不同結果
- (D) R語言與 Python 語言中的數字、字串、矩陣都是物件,但函數不是物件
**答案：D**

## 27. 關於合法的R語言識別符號,下列敘述哪一項錯誤?
- (A) 變數名稱中可以用底線
- (B) 變數名稱避免使用內建的函數/函式名稱
- (C) 變數名稱可以使用數字開頭
- (D) 變數名稱不能使用運算符號當開頭
**答案：C**

## 28. 如附圖所示,在Python中,x為Pandas 的DataFrame 物件,請問如何取出 10?
| | name | price | cost |
|---|---|---|---|
| 0 | apple | 30 | 12 |
| 1 | orange | 8 | 5 |
| 2 | banana | NaNa | 5 |
| 3 | lemon | 20 | 10 |
- (A) `x.iloc[3,2]`
- (B) `x.loc[3,2]`
- (C) `x.loc[3,3]`
- (D) `x.iloc[3,3]`
**答案：A**

## 29. 如附圖所示為 Python 程式碼片段,其執行結果下列哪一項正確?
```python
1 x = 'Scikit-learn is an Open source Machine Learning learning
2 library that supports supervised and unsupervised learning.'
x.find('LEARNING')
```
- (A) 0
- (B) -1
- (C) 7
- (D) 48
**答案：B**

## 30. 關於R語言隱式迴圈(implicit loop) `apply` 系列函數,下列敘述哪一項錯誤?
- (A) `mapply()`:可施加一個函數於多個串列或向量的對應元素上
- (B) `sapply()`:此函數在必要時將簡化 `lappy()`函數傳回的資料物件
- (C) `lapply()`:可使用在二維向量上
- (D) `tapply()`:可以對資料進行分組後進行摘要統計
**答案：C**

## 31. 如附圖所示為R語言的二維矩陣,執行到下列哪一行程式碼之後,會改變維度?
```R
a <- matrix(1:9, nrow=3)
b <- matrix(10:18,nrow=3)
```
- (A) `a+b`
- (B) `colMean(a)`
- (C) `sqrt(a)`
- (D) `a%*% b`
**答案：D**

## 32. 如附圖所示為 Python 的串列(List),若要進行串列相加(X+Y),其執行結果下列哪一項正確?
```python
X = [1, 2, 3, 4]
Y = [5, 6, 7, 8]
```
- (A) [1, 2, 3, 4, 5, 6, 7, 8]
- (B) [1, 5, 2, 6, 3, 7, 4, 8]
- (C) [15, 26, 37, 48]
- (D) [6, 8, 10, 12]
**答案：A**

## 33. 如附圖所示,使用Python 語言建立 `mydict` 物件,圖中 `for loop` 的執行結果下列哪一項正確?
```python
mydict = {
    "uid": 7,
    "login": "userone",
    "name" : 'ipasbigdata'
}

for x in mydict:
    print(x)
```
- (A)
```
uid
login
name
```
- (B)
```
0
1
2
```
- (C)
```
7
userone
ipasbigdata
```
- (D)
```
'uid': 7
'login': 'userone'
'name': 'ipasbigdata'
```
**答案：A**

## 34. 關於 Python 的運用,下列哪一個敘述會跳出本次迴圈,繼續執行下一個迴圈?
- (A) next
- (B) break
- (C) continue
- (D) try
**答案：C**

## 35. 如附圖所示之 Python 程式碼,其執行結果 `total` 值下列哪一項正確?
```python
total = i = 1
n=5
while(i<=n):
    total *= i
    i+=1
print(total)
```
- (A) 5
- (B) 24
- (C) 120
- (D) 720
**答案：C**

## 36. 如附圖所示之 Python 程式碼,假設變數`a`的值為3,其執行結果下列哪一項正確?
```python
if (a==5):
    print("1",end="")
elif (a!=3):
    print("2",end="")
else:
    print("3",end="")
```
- (A) 1
- (B) 2
- (C) 3
- (D)無輸出內容
**答案：C**

## 37. 下列哪一項 Python 程式碼無法將全域變數 `one` 的內容從串列[1]改變成串列[2]?
- (A)
```python
one=[1]
def a():
    one[0]=2
a()
```
- (B)
```python
one=[1]
def b():
    one=[2]
b()
```
- (C)
```python
one=[1]
def c():
    global one
    one[0]=2
c()
```
- (D)
```python
one=[1]
def d():
    global one
    one=[2]
d()
```
**答案：B**

## 38. 如附圖所示為 Python 程式碼片段,其執行結果下列哪一項正確?
```python
def myappend(element, array=[]):
    array.append(element)
    return array

ans = myappend(3, [1,2])
ans = myappend(4)
ans = myappend(7, [5,6])
ans = myappend(8)
print(ans)
```
- (A) [8]
- (B) [[5,6],7,8]
- (C) [4,8]
- (D) [[1,2],3,4,[5,6],7,8]
**答案：C**

## 39. 如附圖所示之 Python 語言的 `for loop`,圖中的紅色框線空白處須輸入下列哪一個函數,才可以正確選取資料包括英文字母的結果?
```python
In: fruits = ["blueberry", "apple", "orange", "grapefruit ", "mango"]
...: mylist = []
...: for x in fruits:
...:     if "a" in x:
...:         ______
...: print(mylist)
['apple', 'orange', 'grapefruit ', 'mango']
```
- (A) `mylist.extend(x)`
- (B) `mylist.insert(x)`
- (C) `mylist.pop(x)`
- (D) `mylist.append(x)`
**答案：D**

## 40. 如附圖所示為 Python 程式碼片段,其執行結果下列哪一項正確?
```python
x = len("Alpaca")
y = len("10001"+"69999")

if x == 10:
    if y > 30:
        print("Ans1")
    else:
        print("Ans2")
else:
    if y == 10:
        print("Ans3")
    else:
        print("Ans4")
```
- (A) Ans1
- (B) Ans2
- (C) Ans3
- (D) Ans4
**答案：C**

## 41. 如附圖所示之 Python 程式碼,其執行結果 `value1`、`value2` 的值下列哪一項正確?
```python
def personal_info(name, *value1, **value2):
    return value1[0], value2

value1, value2 = personal_info('Oscar', '2022-01-01', 'Saturday', gender='male', city='Taipei')
```
- (A) `value1` 的值為'Oscar',`value2` 的值為('gender': 'male', 'city': 'Taipei')
- (B) `value1` 的值為'2022-01-01',`value2` 的值為('male', 'Taipei')
- (C) `value1` 的值為'2022-01-01',`value2` 的值為{'gender': 'male', 'city': 'Taipei'}
- (D) `value1` 的值為'Saturday',`value2` 的值為{'gender': 'male', 'city': 'Taipei'}
**答案：C**

## 42. 如附圖所示為 Python 程式碼片段,其執行結果下列哪一項正確?
```python
balance = 1000
def account_balance (deposit=0, withdrawal=0):
    global balance
    balance = 3000
    balance += deposit
    balance -= withdrawal
    print('balance: ', balance)

account_balance(600)
print('balance: ', balance)
```
- (A)
```
balance: 3600
balance: 3600
```
- (B)
```
balance: 3600
balance: 1000
```
- (C)
```
balance: 2400
balance: 2400
```
- (D)
```
balance: 1600
balance: 1000
```
**答案：A**

## 43. 下列哪一項操作「無法」增加 Map/Reduce 的效能?
- (A) 盡可能的將任務數量加多,使每個任務做的事情越少越好
- (B) 使用具有 in-memory 功能的運算框架,有助於迭代運算
- (C) 對於資料庫存寫,若框架有提供 partition 層級的 Map 操作,應盡量使用,以免增加不必要的資料庫開關操作
- (D) 如果 Map 階段的產出過大,則需要較多數目的 Reducer 來處理,以免所有運算最後擠在少數節點中
**答案：A**

## 44. 相較於其他程式語言,下列哪一項屬於R的特性?
- (A) 沒有物件導向的概念
- (B) 無法快速有效率的處理巨量資料
- (C) 無法進行分散式運算
- (D) 探索式資料分析、資料探勘等,皆可透過 R 語言達成
**答案：D**

## 45. 下列哪一項「不」是 Spark 的執行模式?
- (A) on job
- (B) on yarn
- (C) on cloud
- (D) standalone
**答案：A**

## 46. 在R語言中,程式碼執行時會產生訊息,下列敘述哪一項錯誤?
- (A) 產生錯誤(errors)訊息時,將繼續執行無錯誤的程式
- (B) 警告(warnings)訊息會說明潛在的問題
- (C) 一般傳回的訊息在於說明代碼輸出的結果
- (D) 產生警告(warnings)訊息時,可繼續執行程式
**答案：A**

## 47. 關於 Hadoop 與 MapReduce 兩種技術關係,下列敘述哪一項錯誤?
- (A) JobTracker 會在 Master 上執行,TaskTracker 則是在 Worker 上運作
- (B) MapReduce可分為「Map」、「Reduce」
- (C) Hadoop 中包含一個 Master 與多個 Worker
- (D) Map 只能在 JobTracker 上執行
**答案：D**

## 48. 如附圖所示為 Python 程式碼片段,其執行結果下列哪一項正確?
```python
1 try:
2     x = 0
3     y = 0
4     z = x/y
5 except RuntimeError:
6     print("執行錯誤")
7 except Exception as el:
8     print(el.args)
9 else:
10    print("執行正確,結果為",z)
```
- (A) 執行錯誤
- (B) 執行正確,結果為 0.0
- (C) ('division by zero',)
- (D) ('MemoryError',)
**答案：C**

## 49. 關於程式碼的錯誤處理,下列敘述哪一項錯誤?
- (A) 撰寫程式時要詳盡記錄,可便於出錯時找尋問題
- (B) 可執行的程式即為正確的程式
- (C) 可先要求程式碼的邏輯正確,再設法提升執行效率
- (D) 可藉由函數輔助處理例外狀況與瞭解錯誤訊息
**答案：B**

## 50. 如附圖所示,在Python 語言中,可以使用 `assert` 進行斷言測試,請問附圖陳述句的測試效果,下列敘述哪一項正確?
```python
assert one==two,three
```
- (A) 當 `one` 與 `two` 不相等或 `one` 與 `three` 不相等時引發錯誤
- (B) 當`one`與 `two` 相等且 `one` 與 `three` 相等時引發錯誤
- (C) 當`one` 與 `two`不相等時,引發錯誤,顯示 `three` 的內容
- (D) 當`one`與 `two` 相等時,引發錯誤,顯示 `three` 的內容
**答案：C**
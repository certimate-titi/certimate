## 1. 當有離群值(Outlier)時,下列哪一項處理方式最正確?
- (A) 將其移除
- (B) 不予理會
- (C) 使用填補法(Imputation)
- (D) 視分析目的而定
**答案：D**

## 2. 關於遺缺值(Missing Value)的處理,下列敘述哪一項正確?
- (A) 即使資料有遺失值也不應該被刪除,所有的資料都應該被完整保存下來
- (B) 同一欄位(column)中太多資料都含有遺缺值時,不適合將這些資料全都刪除,應該找尋補齊遺缺值的方法
- (C) 如果類別變量有遺缺值,則可以使用算術平均數填補該遺缺值
- (D) 不論資料分布型態,皆可直接以資料中非缺失值的平均數或中位數來補齊缺失值
**答案：B**

## 3. 下列哪一項「不」是資料前處理的步驟?
- (A) 資料清理(Data Cleaning)
- (B) 資料整合(Data Integration)
- (C) 資料建模(Data Modeling)
- (D) 資料變形(Data Reshaping)
**答案：C**

## 4. 下列哪一項是最「不」適合填補遺缺值(Missing Value)的方式?
- (A) 熱卡填補法(Hot Deck Imputation)
- (B) 迴歸填補法(Regression Imputation)
- (C) 填補最大值
- (D) 平均值填補(Mean/Mode Completer)
**答案：C**

## 5. 若要檢查 E-mail 格式是否符合(如:qoo5205566@gmail.com),下列哪一種正則表達式(Regular Expression)可正確判斷?
- (A) `^([a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4})*$/`
- (B) `^([a-zA-Z0-9._%-]+[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4})*$/`
- (C) `+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4})*$/`
- (D) `^([a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]*$/`
**答案：A**

## 6. 下列哪一項「不」是SQL 中的聚合函數(Aggregate function)?
- (A) count
- (B) sum
- (C) avg
- (D) cast
**答案：D**

## 7. 下列哪一項「不」是非監督式學習的常見方法?
- (A) 主成分分析(Principal Components Analysis)
- (B) 非計量多向度量尺法(Non-metric Multidimensional Scaling)
- (C) 對應分析(Correspondence Analysis)
- (D) 線性判別分析(Linear Discriminant Analysis)
**答案：D**

## 8. 下列哪一種圖形化方法,能直觀的觀察資料集中,不同變數之間的關聯性?
- (A) 勝率比(Odds ratio)
- (B) 平行座標軸(Parallel coordinates)
- (C) 目標投影追蹤(Targeted projection pursuit)
- (D) 平均數全距管制圖(X-bar range control chart)
**答案：B**

## 9. 關於敘述統計的方法,下列哪一項錯誤?
- (A) 敘述統計是為了瞭解資料的頻率、趨勢、離散程度等特徵的一種方法
- (B) 觀察資料的分布、集中特性,如中位數、眾數、平均數、標準差也都是一種敘述統計方法
- (C) 集群分析 K-means Clustering 是一種將資料分類觀察的敘述統計方法
- (D) 圖示法,如:直方圖、餅圖、散點圖等,都是一種敘述統計方法
**答案：C**

## 10. 下列是進行資料去識別化的動作,請問哪一個行為較「不」恰當?
- (A) 將只有唯一一個值的欄位刪去
- (B) 將性別的資料男和女轉為0和1
- (C) 模擬某欄位的資料分布,重新佈署資料,以保有資料的原有特徵
- (D) 將性別欄位和年齡欄位隨機混合在一起
**答案：D**

## 11. 下列哪一項是監督式(Supervised)的特徵工程(Feature Engineering)方法?
- (A) 線性判別分析(Linear Discriminant Analysis)
- (B) 主成分分析(Principal Component Analysis)
- (C) 潛在語意分析(Latent Semantic Analysis)
- (D) 獨立成分分析(Independent Component Analysis)
**答案：A**

## 12. 下列哪一種類型資料,適合使用資料增益(Information Gain, IG) 進行特徵選取(Feature Selection)?
- (A) 擁有大量不同數值的資料特徵
- (B) 名目(Nominal)的資料特徵
- (C) 非離散化的數值特徵
- (D) 連續型的數值
**答案：B**

## 13. 在使用線性模型時,下列哪一種方法用來將名目(Nominal)類型資料轉換為實數(Real Number)類型資料,可以最公平的進行轉換而沒有對特定的可能值(Possible Value)造成偏差?
- (A) 直接將所有不同數值轉為單一維度的布林值,如將性別(男、女)轉為二維向量男=(1,0)及女= (0,1)
- (B) 依照名目(Nominal)類型資料的數值資訊轉為相對應的實數值,如將體重(過重、一般、過輕)轉為(1,0,-1)
- (C) 直接將特徵值給予對應的實數值,如將天氣(晴、陰、雨)轉為(0,1,2)
- (D) 依照特徵值給予範圍內隨機數值,如里程(遠、中、近)分別給予100~1000(遠)、50~100(中)、0~50 (近)的隨機數值
**答案：A**

## 14. 在資料準備時,下列敘述哪一項錯誤?
- (A) 資料準備時,經過資料整合、清理、轉換、減少等步驟架構良好的資料
- (B) 資料整合包括蒐集資料、選擇資料、整合資料
- (C) 資料清理不包括減少變數數目、消除不一致、平衡偏斜資料
- (D) 資料轉換包括正規化資料、分散/整合資料、建構新屬性
**答案：C**

## 15. 關於特徵(屬性)萃取(Feature Extraction)與轉換(Transformation),下列敘述哪一項正確?
- (A) 資料縮減泛指屬性挑選(Selection)與萃取(Extraction)
- (B) 屬性越多,表示後續建模有越多參數要調校,過度配適(Overfitting)的風險越低
- (C) 各屬性的量綱均一化屬於屬性萃取(Extraction)的工作
- (D) 主成分分析(Principal Component Analysis, PCA) 是分佈偏斜屬性常用的轉換方法
**答案：A**

## 16. 如附圖所示之程式碼,若使用 XPath 的語法要選擇在 plate 標籤層下的 apple,下列哪一項錯誤?
```xml
<div class="table">
<bento></bento>
<plate>
<apple><apple/>
</plate>
<apple><apple/>
<div>
```
- (A) `//plate/apple`
- (B) `/div/plate/apple`
- (C) `/plate/apple`
- (D) `//apple[1]`
**答案：C**

## 17. 若要確保巨量資料運算平台之服務,不會因為單點毀損導致無法存取服務(Single Point of Failure, SPOF),我們會進行高可用性(High Availability, HA)的設計,關於HA的敘述,下列哪一項錯誤?
- (A) 服務層級協議(Service-Level Agreement)決定連續不中斷服務的程度,等級越高表示服務等級越高
- (B) Hadoop 上的HDFS (Hadoop Distributed File System)的高可用性可透過配置 Active/Active 兩個 NameNodes 節點解決 SPOF 問題
- (C) 可以透過 JournalNode 的設計來儲存 HDFS(Hadoop Distributed File System)文件的紀錄,若發生 NameNode 損壞,新的 NameNode 可透過此紀錄恢復既有的文件紀錄
- (D) 具備有高可用性的架構下,發生 NameNode 損壞時,運行中的程式不受影響,仍會繼續完成工作
**答案：B**

## 18. 如附圖所示,Hadoop 最基本架構包含下列哪些項目?
(1) Spark
(2) HDFS
(3) MapReduce
(4) Hive
- (A) (1)和(2)
- (B) (2)和(3)
- (C) (3)和(4)
- (D) (1)(2)(3)(4)
**答案：B**

## 19. 若要取得某一網頁的資料,下列哪一個方法最正確?
- (A) UPDATE
- (B) HEAD
- (C) PUT
- (D) GET
**答案：D**

## 20. 如附圖所示,有一個 data 數列,請問經過 MapReduce 模型處理的結果,下列哪一項正確?
```
data = [1,2,3,4,5]
data.map(x => x * x).reduce(x, y => x + y)
```
- (A) 15
- (B) 55
- (C) 25
- (D) 49
**答案：B**

## 21. 如附圖所示為某產品每月市場需求的機率分配,請問該產品每月需求量之期望值,下列哪一項正確?
| 需求個數 | 230 | 360 | 460 | 500 |
|---|---|---|---|---|
| 機率 | 0.2 | 0.35 | 0.25 | 0.20 |
- (A) 387
- (B) 420
- (C) 299
- (D) 361
**答案：A**

## 22. 若隨機變數X服從二項分配(Binomial Distribution),其每次試驗成功的機率為0.4,試驗次數為10次,則X的期望值與變異數,下列哪一項正確?
- (A) 期望值為2與變異數為 1.2
- (B) 期望值為2與變異數為2.4
- (C) 期望值為4 與變異數為 1.2
- (D) 期望值為4與變異數為2.4
**答案：D**

## 23. 某品牌燈泡平均壽命為1200 小時,標準差為36小時。現購買此燈泡 36 隻,若Z為標準常態分配,請問此 36 支燈泡壽命至少為1180 小時的機率,下列哪一項正確?
- (A) $Pr(Z > -2.2)$
- (B) $Pr(Z > -2.4)$
- (C) $Pr(Z > -2.6)$
- (D) $Pr(Z > -2.8)$
**答案：待匹配**
答案修正
本題為計算 36支燈平均泡壽命,即
$$\bar{X} \sim N \left(\mu, \frac{\sigma^2}{n}\right)$$
$$P(\bar{X} \ge 1180) = P \left(Z \ge \frac{1180 - 1200}{\frac{36}{\sqrt{36}}}\right) = P(Z \ge -3.33)$$

## 24. 某公司所生產10公斤裝的糖果,其標準差為0.4公斤,欲估計母體平均數。若Z為標準常態分配,且$Pr(Z<-1.96) = 2.5\%$,在95%信賴水準下,使估計誤差不超過0.08公斤,至少應抽多少包糖果來秤重?
- (A) 62包
- (B) 75包
- (C) 97包
- (D) 116包
**答案：C**

## 25. 有一個隨機樣本數據為:1,3,5,9,11,13,下列敘述哪一項正確?
- (A) 全距為5
- (B) 眾數為7
- (C) 中位數為5
- (D) 平均數為7
**答案：D**

## 26. 如附圖所示為 Python 語言,mydist 函數回傳是什麼結果?
```python
def mydist(a,b):
    return abs(a[0]-b[0])+abs(a[1]-b[1])

print(mydist((1,1),(2,2)))
```
- (A) 歐幾里得距離(Euclidean distance)
- (B) 曼哈頓距離(Manhattan distance)
- (C) 馬氏距離(Mahalanobis distance)
- (D) 餘弦相似(Cosine similarity)
**答案：B**

## 27. 某公司生產的燈泡有 10%的不良率。此公司為了品質對每一個燈泡做檢驗,將其分類為「通過」或「不通過」。若檢驗員有5%的機會分類錯誤,則下列哪一項是被分類為「不通過」的百分比?
- (A) 12%
- (B) 14%
- (C) 16%
- (D) 18%
**答案：B**

## 28. 關於關聯法則的敘述,下列哪一項錯誤?
- (A) 為找出所有頻繁項目集與找出頻繁項目集中具有強關聯規則的規則
- (B) 從數量低的集合開始,當發現該集合不是頻繁的,則它的母集反而需要考慮
- (C) FP-growth 算法比 Apriori 算法更有效率
- (D) 當資料集很大時,Apriori 算法需要不斷掃描資料集造成運行效率很低
**答案：B**

## 29. 關於線性迴歸與邏輯斯迴歸,下列敘述哪一項錯誤?
- (A) 線性迴歸的應變數連續型,邏輯斯迴歸應變數是類別型
- (B) 線性迴歸的應變數和自變數之間的關係假設是線性相關的,邏輯斯迴歸的應變數和自變數是非線性的
- (C) 線性迴歸應變數y的觀察值是服從常態分布的;邏輯斯迴歸應變數 y是服從二項分布0和1或者多項分布的
- (D) 關於係數估計,線性迴歸採用最大似然法(Maximum Likelihood, ML),邏輯斯迴歸採用最小平方法(Least Square, LS)
**答案：D**

## 30. 下列哪一個觀念錯誤?
- (A) 計算全國失業率時,為了降低誤差,全面調查的結果最為精準
- (B) 計算全國失業率時,以抽樣方法可以減少計算成本
- (C) 計算全國失業率時,以抽樣方法會有計算誤差
- (D) 計算全國失業率時,以台北市的失業率直接推算其他五個直轄市(新北、桃園、台中、台南、高雄)的失業人數,是精確的估計方法
**答案：D**

## 31. 關於PCA 主成分分析與 SVD 奇異值分解的比較,下列敘述哪一項正確?
- (A) PCA 較 SVD 更一般化
- (B) SVD 提供資料矩陣只有橫列的基底
- (C) PCA 提供資料矩陣之綜行與橫列的基底
- (D) SVD 較 PCA 更一般化
**答案：D**

## 32. 如附圖所示為R語言,執行 ggplot2 套件視覺化分析,下列敘述哪一項正確?
```R
ggplot(mtcars, aes(hp, mpg)) +
  geom_point() +
  geom_smooth(method = "lm")
```
![Scatter plot of mpg vs hp](image.png)
- (A) hp 與 mpg 變數呈現正相關
- (B) 使用以下函數可繪製題目之結果
- (C) hp 與 mpg 變數無明顯相關性
- (D) 使用以下函數可繪製題目之結果
**答案：D**

## 33. 若有兩個向量 $A=<2,0,0>, B = <2,2,1>$;請問這兩個向量之間的餘弦(Cosine)相似度最接近下列哪一個數字?
- (A) 0.67
- (B) 0.33
- (C) 1
- (D) 0.5
**答案：A**

## 34. 關於主成分分析(Principal Component Analysis, PCA)屬性萃取的主要用途,下列哪一項正確?
- (A) 萃取出重要的主要主成分後,可以長條圖視覺化多變量資料
- (B) 可將低度相關的預測變數矩陣 X,轉換成相關且量多的潛在變數集合
- (C) 可將最攸關的訊息與無關的雜訊結合
- (D) 可將問題領域中的數個變數,組合成單一或數個具訊息力的特徵變數
**答案：D**

## 35. 下列哪一項集群方法,可以解決資料中有離群值及類別屬性的問題?
- (A) K 平均法(K-means)
- (B) K 代表點(K-medoids)
- (C) K近鄰(K nearest neighbor)
- (D) K奇異值分解(K-singular value decomposition)
**答案：B**

## 36. 在 R語言中使用 arules 套件,下列哪一個指令可顯示關聯規則的支持度(Support)、信賴度(Confidence)與增益(Lift)結果?
- (A) view
- (B) quality
- (C) exam
- (D) show
**答案：B**

## 37. 關於探索式資料分析,下列哪一個是常用來觀察極端值的分佈?
- (A) 雷達圖(Radar Chart)
- (B) 泡泡圖(Bubble Chart)
- (C) 盒鬚圖(Box Plot)
- (D) 桑基圖(Sankey Diagram)
**答案：C**

## 38. 關於探索式資料分析,下列哪一個最常用來呈現時間資料趨勢的概念?
- (A) 圓餅圖(Pie Chart)
- (B) 三元平衡圖(Ternary Plots)
- (C) 直方圖(Histogram)
- (D) 折線圖(Line Chart)
**答案：D**

## 39. 關於非監督式學習(Unsupervised Learning),下列敘述哪一項錯誤?
- (A) 在資料集內之變數中,沒有預測目標
- (B) 資料劃分為集群,可理解各集群的特性
- (C) 迴歸分析和 K-means 兩種演算法常被用來進行資料的分類
- (D) 變數間的關係與資料的樣式(Pattern),找出資料間分佈的趨勢
**答案：C**

## 40. 關於K平均法(K-means),下列敘述哪一項錯誤?
- (A) 需給定K群,並隨機挑選K個點作為群集中心,亦可給定既有的點來挑選
- (B) 分群的好壞在於組內變異(within)的值要小,表示同一群裡面的點離散程度小、較密集
- (C) 亦可用亂度或是密度來測量取代距離,規律的數據結構下,亂度值是低的,而隨機性的數據結構的亂度值則是高的
- (D) 分群後的結果,部分的點可能會分配到多個不同的群
**答案：D**

## 41. 關於常用的決策樹(Decision Tree)演算法,下列哪一項錯誤?
- (A) ID3 (Iterative Dichotomiser 3)
- (B) C4.5
- (C) CART (Classification and Regression Tree)
- (D) OLSR (Ordinary Least Squares Regression)
**答案：D**

## 42. 關於線性迴歸模型的敘述,下列哪一項錯誤?
- (A) 線性迴歸方程式,其資料分布之趨勢線不一定是直線
- (B) 資料共線性(Multicollinearity)問題,不會影響線性迴歸模型的優化
- (C) 若某資料為標準常態分佈(Standard Normal Distribution),則其標準差(Standard Deviation)為1
- (D) 在訓練模型時,需要注意是否出現過度配適(Overfitting)的情形
**答案：B**

## 43. 在簡單線性迴歸模型(Linear Regression)當中,斜率的估計值代表下列哪一種意義?
- (A) 觀察值的預測值
- (B) 當自變數變動一單位時,依變數的平均變動估計值
- (C) 當自變數為0時,依變數的估計值
- (D) 當自變數為0時,依變數的平均估計
**答案：B**

## 44. 監督式學習(Supervised Learning)「不」包含下列哪一項?
- (A) 分類(Classification)
- (B) 推估(Estimation)
- (C) 預測(Prediction)
- (D) 分群(Clustering)
**答案：D**

## 45. 機器學習模型中,關於模型的偏差(bias)與變異(variance),下列敘述哪一項正確?
- (A) 高偏差代表模型過於複雜
- (B) 高變異代表模型過於簡單
- (C) 模型訓練的目標為低偏差與高變異
- (D) 偏差與變異之間存在抵換(trade-off)關係
**答案：D**

## 46. 下列哪一項「不」屬於監督式學習(Supervised Learning)?
- (A) K平均法(K-Means)
- (B) 決策樹(Decision Tree)
- (C) 支援向量機(Support Vector Machine, SVM)
- (D) 邏輯迴歸(Logistic Regression)
**答案：A**

## 47. 如附圖所示,關於二元分類(binary classification),若一分類模型產生之混淆矩陣(confusion matrix),該模型之精確度(precision)為下列哪一項?
| | 正確答案 | |
|---|---|---|
| | True | False |
| 預測結果 | True | 8 | 3 |
| | False | 12 | 11 |
- (A) 3/11
- (B) 8/20
- (C) 19/34
- (D) 8/11
**答案：B**

## 48. 使用線性模型(Linear Model)方法時,針對稀疏資料(Sparse data),最適合使用下列哪一種處理方式?
- (A) 核方法(Kernel Method)
- (B) 過採樣(Over Sampling)
- (C) 降採樣(Down Sampling)
- (D) 交叉驗證(Cross Validation)
**答案：A**

## 49. 如附圖所示,針對同一份資料建立的四種複迴歸模型,根據各種模型之指標資訊,請問下列哪一個為最佳模型?
| 模型編號 | 模型 | AIC | BIC | Cp | R$^2$ |
|---|---|---|---|---|---|
| 模型1 | $y = \beta_0 + \beta_1x_1 + \beta_2x_2 + \epsilon$ | -55 | 50 | 3 | 0.8 |
| 模型2 | $y = \beta_0 + \beta_1x_1 + \beta_2x_2 + \beta_3x_3 + \epsilon$ | -55 | 50 | 4 | 0.8 |
| 模型3 | $y = \beta_0 + \beta_1x_1 + \beta_2x_2 + \epsilon$ | -30 | 60 | 3 | 0.8 |
| 模型4 | $y = \beta_0 + \beta_1x_1 + \beta_2x_2 + \beta_3x_3 + \epsilon$ | 10 | 100 | 3 | 0.8 |
AIC 為赤池信息量準則(Akaike Information Criterion);
BIC 為貝葉斯信息準則(Bayesian Information Criterion);
Cp為馬洛斯Cp (Mallows'Cp);
R$^2$為判定係數(coefficient of determination)
- (A) 模型1
- (B) 模型2
- (C) 模型3
- (D) 模型4
**答案：A**

## 50. 關於監督式學習(Supervised Learning)常用的演算法,下列敘述哪一項錯誤?
- (A) Linear Regression 可以建立自變數與應變數的關係
- (B) LASSO 是迴歸演算法的延伸,對於精簡的模型有較高的獎勵,並懲罰較複雜的模型
- (C) 隨機森林是多棵決策樹的集成模型
- (D) SVM 在特定條件下,可以將資料維度映射到低維度上,藉此找到較佳的分類方式
**答案：D**
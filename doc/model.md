# モデルについて

## 変数
まず、以下のような変数を定義します。
* p: shifter's name
* a: shifter's attribute
* d: shift day
* t: shift time
* s: shift work

これらの変数を引数に取る変数$x$を定義します。
<!--
$$
x(p,~a,~d,~t,~s) = \begin{cases}
    1 & (\mathrm{person\ (p,~a)\ takes\ (d,~t,~s)\ shift}) \\
    0 & (\mathrm{otherwise})
  \end{cases}
$$
-->
```math
x(p,~a,~d,~t,~s) = \begin{cases}
    1 & (\mathrm{person\ (p,~a)\ takes\ (d,~t,~s)\ shift}) \\
    0 & (\mathrm{otherwise})
  \end{cases}
```

<!--
この変数$x$を、全ての$(p,~a,~d,~t,~s)$の組み合わせで考えます。
-->
この変数$`x`$を、全ての$`(p,~a,~d,~t,~s)`$の組み合わせで考えます。

## 目的関数
最適化として、最小化する関数を
$$
\sum_{(p,a)\in P}\sum_{(d,t,s)\in S}x(p,~a,~d,~t,~s)
$$
と定義します。
ここで、シフターの集合を$P$、シフト業務の集合を$S$としました。

これを最小化するということは、この後のべる拘束条件を満たす中で、シフトに入る人の数が最小になるようにするといった条件と考えることができます。


## 拘束条件

### default
* **一つのシフトには必ず一人以上が入る**
$$
\sum_{(p,a)\in P}x(p,~a,~d,~t,~s) \ge 1\ (\mathrm{for\ each}\ (d,t,s))
$$ 

* **一つの時間スロットには同じ人が入らないようにする**
$$
\sum_{s}x(p,~a,~d,~t,~s) \le 1\ (\mathrm{for\ each}\ (p,a,d,t))
$$

* **NGのスケジュールには入らないようにする**

NGスケジュールの集合を作成し、$N$と名付けるとすると、
$$
x(p,~a,~d,~t,~s) = 0\ (\mathrm{when}\ (p,~a,~d,~t,~s)\in N)
$$

### option
* **連続のシフトを禁止する**

同じ日付$(d)$の連続する時間$(t_1, t_2)$に対して、
$$
\sum_{s}x(p,~a,~d,~t_1,~s)+\sum_{s}x(p,~a,~d,~t_2,~s) \le 1\ (\mathrm{for\ each}\ (p,a,d))
$$

* **イベント全体での最大シフト数を決める**

最大シフト数を$N_{max}$とすると、
$$
\sum_{(d,t,s)\in S}x(p,~a,~d,~t,~s) \le N_{max}\ (\mathrm{for\ each}\ (p,a))
$$

* **各日での最大シフト数を決める**

各日での最大シフト数を$n_{max}$とすると、
$$
\sum_{t,s}x(p,~a,~d,~t,~s) \le n_{max}\ (\mathrm{for\ each}\ (p,a,d))
$$

* **attributeで指定されるグループの人がshiftで表される仕事に入らなければならない**

特定のattributeを$a_1$、特定の仕事を$s_1$と表すと、
$$
\sum_{p}x(p,~a_1,~d,~t,~s_1) \ge 1\ (\mathrm{for\ each}\ (d,t))
$$

* **attributeで指定されるグループの人が、shiftで表される仕事を避ける**

特定のattributeを$a_2$、特定の仕事を$s_2$と表すと、
$$
\sum_{p}x(p,~a_2,~d,~t,~s_2) = 0\ (\mathrm{for\ each}\ (d,t))
$$

* **attributeで指定されるグループの人がday, timeで指定されるスロットを避ける**

特定のattributeを$a_3$、特定の日付、時間を$d_3, t_3$と表すと、
$$
\sum_{p}x(p,~a_3,~d_3,~t_3,~s) = 0\ (\mathrm{for\ each}\ s)
$$
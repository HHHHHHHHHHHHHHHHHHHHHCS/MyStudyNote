写写简单的HBAO
======

(Github正常排版: [写写简单的HBAO][1])

-----------------


<!-- @import "[TOC]" {cmd="toc" depthFrom=1 depthTo=6 orderedList=false} -->

<!-- code_chunk_output -->

- [**0. 起因**](#0-起因)
- [**1. 原理**](#1-原理)

<!-- /code_chunk_output -->



-----------------

## **0. 起因**

URP有SSAO, HDRP有GTAO. 所以摆烂学一个HBAO.

下面是效果图.

![](Images/HBAO_00.jpg)

![](Images/HBAO_01.jpg)

就不放和其它AO对比图了, 调参有点麻烦. 直接进行一个照搬.

![](Images/HBAO_02.jpg)


HBAO对比SSAO采样次数更少, 效果也好很多. 虽然可以用TSSAO来减少采样和降低噪点.

-----------------

## **1. 原理**

HBAO, Image-Space Horizon-Based Ambient Occlusion, 水平基准环境光遮蔽, 是一项英伟达于2008年提出的SSAO衍生版, 效果比SSAO更好. [文章地址][2]

YiQiuuu的有篇文章是关于HBAO原理和实现, 讲的详细且不错, [文章地址][3]. 这里直接快速引用概括一下.


1. 屏幕上的每一个像素, 做一个四等分的四条射线, 然后随机旋转一下. 每一个像素的随机角度不能一样, 否则效果很怪(是错的).

![](Images/HBAO_03.jpg)

2. 对于任意一个方向, 沿着射线方向生成一个一维的高度. 然后根据深度做RayMarch找到一个最大的水平角(Horizon Angle).

![](Images/HBAO_04.jpg)

3. 根据点P和它的法线(面法线), 计算它的切面角(Tangent Angle).

![](Images/HBAO_05.jpg)

4. 根据Horizon Angle和Tangent Angle, 得到AO. AO = sin(h) - sin(t).

至于为什么AO=角度差值? 我的理解(个人理解)是 周围的东西对比当前点越高, 则表示光被周围东西遮挡的越多, 则越暗.

![](Images/HBAO_06.jpg)

为什么用面法线, 而不是顶点插值法线?

![](Images/HBAO_07.jpg)

看官网的PPT是说 如果用顶点插值法线去计算会得到错误的遮挡.

如果我们用的是顶点插值法线, 当P在边界位置的时候, 计算的半球起始位置就可能会是错的.

而根据View Space 利用ddx/ddy重新生成的法线是对的, 之前的SSAO篇中有介绍怎么重新生成法线.

-----------------

-----------------

Low-Tessellation问题
bias

不连续问题
衰减

噪声
blur


-----------------

[1]:https://github.com/HHHHHHHHHHHHHHHHHHHHHCS/MyStudyNote/blob/main/MyNote/%E5%86%99%E5%86%99%E7%AE%80%E5%8D%95%E7%9A%84HBAO.md
[2]:https://developer.download.nvidia.cn/presentations/2008/SIGGRAPH/HBAO_SIG08b.pdf
[3]:https://zhuanlan.zhihu.com/p/103683536


https://blog.csdn.net/qjh5606/article/details/120001743

https://www.csdn.net/tags/MtTaAg2sOTIzOTM4LWJsb2cO0O0O.html

https://zhuanlan.zhihu.com/p/367793439
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


-----------------

## **1. 原理**

HBAO, Image-Space Horizon-Based Ambient Occlusion, 水平基准环境光遮蔽, 是一项英伟达于2008年提出的SSAO衍生版, 效果比SSAO更好。

YiQiuuu的有篇文章是关于HBAO原理和实现, 讲的详细且不错, [文章地址][2]. 这里直接快速引用概括一下.


第一步, 屏幕上的每一个像素, 做一个四等分的四条射线, 然后随机旋转一下. 每一个像素的随机角度不能一样, 否则效果很怪(是错的).

![](Images/HBAO_03.jpg)


比SSAO对于每一个着色点需要进行64次（取决于随机点数量）采样，这对于移动端硬件来说采样率太高了（但可以用TSSAO来进行时空复用），因此目前手机主流的是采用HBAO来做环境遮蔽，而HBAO不仅减少了采样数量而且效果甚至也比SSAO更好（解决SSAO遮挡时不部分深度错误的情况）。

-----------------

[1]:https://github.com/HHHHHHHHHHHHHHHHHHHHHCS/MyStudyNote/blob/main/MyNote/%E5%86%99%E5%86%99%E7%AE%80%E5%8D%95%E7%9A%84HBAO.md
[2]:https://zhuanlan.zhihu.com/p/103683536
写轮眼个CapsuleAO
======

(Github正常排版: [写轮眼个CapsuleAO][1])

-----------------


<!-- @import "[TOC]" {cmd="toc" depthFrom=1 depthTo=6 orderedList=false} -->

<!-- code_chunk_output -->

- [**0. 起因**](#0-起因)
- [**1. 原理**](#1-原理)
- [**2. 先写个Capsule**](#2-先写个capsule)

<!-- /code_chunk_output -->


-----------------

## **0. 起因**

无(you)意间看到了一个Capsule AO插件, 正好学一下(Ctrl+C+V). 请多多支持正版, 我只做学习笔记. [插件地址][2]

![](Images/CapsuleAO_00.jpg)

我使用CapsuleAO, 最主要是想要生成影中影和贴近墙壁地板的AO的效果.

UE的Docs上有一个很好的对比图, 比我不知道高到哪里去了. [对比地址][3]. 建议抄UE的代码.

![](Images/CapsuleAO_01.jpg)

-----------------

## **1. 原理**

一句话概括本文的原理, 用胶囊体(Capsule)来替代角色的躯干去模拟Shadow和AO. Screen的WorldPos沿着WorldNormal和LightDir对Capsule做射线检测, 从而产生AO和Shadow.

![](Images/CapsuleAO_02.jpg)

下面内容主要参考(Copy) 简书的 离原春草 的 [Ambient Occlusion技术方案综述][4] 的 CapsuleAO.

雏形是 [Ren2006] & [Sloan 2007] 中用球谐函数SH来对球形遮挡体的可见性进行模拟的. 但是长距离软影, 至少需要2阶球谐函数, 消耗过高. 所以顽皮狗的Michal Iwanicki 在 [SIGGRAPH2013][5] 提出了 Capsule AO. 

CapsuleAO的基础技术原理用球是相似的. 效果主要由AO(Ambient term)和Shadow(Directional term)组成.

AO: 球在半球上投影面积比例.

Shadow: 发射点沿着LightDir 产生一个圆锥(锥角由我们决定, 效果是阴影的软化程度). 球和圆锥的相交面积比例.

![](Images/CapsuleAO_03.png)

![](Images/CapsuleAO_04.png)

还有一个预计算贴图, 用于Directional term, 是蒙特卡洛算法在离线时预计算出遮挡体与被渲染点几何关系与遮挡值的函数关系. 因为那时是PS3时代, ALU不足, 用贴图采样取代复杂的算法. **但是这篇文章的代码里面并没有用到这个图**.

对于一个给定的锥角而言, 遮挡值可以用遮挡体对于当前点的张角(\theta)以及到球心的射线与椎体轴线夹角(\phi)的函数来表示, 这个结果被存成像上面一样的贴图里. 对于不同的锥角, 可分别输出2D贴图, 然后组成3D贴图.

![](Images/CapsuleAO_05.png)

不同的锥角影响着阴影的软化程度, 锥角越大, 软化程度越高。

还有一堆数学公式的可以直接看这篇文章, [文章地址][6].

-----------------

## **2. 先写个Capsule**

可以尝试写一下Shader toy 上面的 Capsule.


-----------------

[1]:https://github.com/HHHHHHHHHHHHHHHHHHHHHCS/MyStudyNote/blob/main/MyNote/%E5%86%99%E8%BD%AE%E7%9C%BC%E4%B8%AACapsuleAO.md
[2]:https://assetstore.unity.com/packages/vfx/shaders/fullscreen-camera-effects/ambient-character-shadows-209214
[3]:https://docs.unrealengine.com/4.27/en-US/BuildingWorlds/LightingAndShadows/CapsuleShadows/Overview/
[4]:https://www.jianshu.com/p/7d0704442306
[5]:http://miciwan.com/SIGGRAPH2013/Lighting%20Technology%20of%20The%20Last%20Of%20Us.pdf
[6]:https://zhuanlan.zhihu.com/p/460444838
https://zhuanlan.zhihu.com/p/368039787
https://www.jianshu.com/p/7d0704442306


character shadow
editor
manager
feature
pass
shader

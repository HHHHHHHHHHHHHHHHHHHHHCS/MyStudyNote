**基于Unity SRP的手游渲染之道**
=================

(Github正常排版: [基于Unity SRP的手游渲染之道](TODO:))

------------------------

[1. 安全与公平](#1)<br>
[2. 游戏体验](#2)<br>
[3. 粒子优化](#3)<br>
[4. 粒子离线模拟](#4)<br>


------------------------
<span id='1'/>

## **1. 渲染知识树**
越往下越底层
* ## **应用图形学算法**
  + 常见Shader
  + 光照模型:Lambert,Phong,BRDF等
  + 后效:Bloom,DOF,SunShaft等
* ## **渲染管线**
  + Forward
  + Deferred
* ## **图形API**
  不同语言有什么区别,不同版本支持什么,新增什么API
  + DX8/9/SM3.0/DX10/11/12
  + OpenGL
  + OpenGLES1.0/2.0/3.0/3.1/3.2
  + Mentel Vulkan
  + Metal1.0/2.0
* ## **GPU底层**
  + 针对不同硬件有什么特点,能做什么不能做什么
  + https://zhuanlan.zhihu.com/p/259760974
  + IMR
  + TBR
  + TBDR
  + 比如:HSR可以解决overdraw,渲染顺序改成状态切换
  + 比如:Early-Z也可以避免一些overdraw,但是远近顺序无法避免,AlphaTest会打断(https://blog.csdn.net/wolf96/article/details/85001484)
  + 比如:drawcall,CPU发送数据给GPU,但是发送的时候CPU还有做检查工作,过多会导致CPU Bound,而Vulkan,Metal少了很多检查所以速度就快了(华为好像也少了很多检查去掉一些兼容性)
<br/>

------------------------
<span id='2'/>

## **2. Why SRP**
1. ## **RT Load/Store Action & Memoryless**
    + https://answer.uwa4d.com/question/5e856425acb49302349a1119
    + https://docs.unity3d.com/ScriptReference/RenderTexture-memorylessMode.html
    + RT 从System Memory Load 到 CPU/GPU Tile Memory 绘制完成 , 再Store回来
    + 设置StoreAction.DontCare/Memoryless,就不会产生带宽
<br/>

2. ## **MSAA**
    + 正常的时候4XMSAA , 造成的带宽是4*RT Size
    + 现在设置RenderTextureMemoryless.MSAA , 利用手机的Tile特性把4x Resolve 成1x , 再store回来 , 这样带宽就是1x RTSize 
    + 再比如可以绘制不透明的时候开MSAA,绘制半透明相关时候关闭MSAA,减少带宽( MSAA 也有其局限之处，比如对于半透明物件、边缘不明确或者非常复杂的物件比如密集草丛、铁丝网这类的抗锯齿处理就比较力不从心,by https://zhuanlan.zhihu.com/p/56385707)
<br/>

3. ## **Instance VS SRP Batcher**
    + PC数据(Instance -> SRP Batcher)
      - Batch:315->65
      - SetPass:113->57
      - CPU:6ms->2.5ms
    + 在低配安卓机上drawcall敏感,SRP Batcher要传入大块的数据,可能更加负优化
    + 不过在ios(metal)上SRP Batcher性能提升明显
<br/>

4. ## **物件渲染顺序的改变成状态变化(HSR)**
    + SortingCriteria.RenderQueue->SortingCriteria.OptimizeStateChanges
    + Batch:250->206  SetPass:122->95
<br/>

5. ## **Framebuffer Fetch**
    + 移动平台在Shader中利用inout关键字可以拿到当前绘制的RT的color和depth
    + 延迟贴花,原来要copy depth RT 再 tex2D, 现在直接inout
    + 软粒子,深度比较原理同上
    + 苹果全系列完美支持MRT和depth
    + ARM-Mali全系列不支持MRT,只能支持RT0和depth
    + 高通-Adreno中高端(Adreno512)支持MRT但是不支持depth,低端机不支持AlphaTest的framebuffer fetch会crash
<br/>

6. ## **隔帧Culling**
    + 减少Culling的消耗.因为渲染线程都要等Unity Culling执行完成之后获取结果进行渲染,所以减少Culling频率
<br/>

7. ## **自定义Culling**
    + Unity原来是暴力遍历全部的物体是否在frustum
      - 优点原生C++代码,4个多线程
    + 八叉树场景管理
    + DrawMeshInstance避免unity自己的渲染排序不确定问题
    + GPU Driven Pipeline , 可以解决CPU Bound
    + 可以自己控制Culling,把渲染线程的等待Culling结果放到逻辑代码中,从而减少线程上的等待
<br/>

8. ## **阴影动静分离**
    + 少绘制阴影,减少drawcall
    + 相机少量移动,通过矩阵推算
<br/>

9. ## **自定义HDR格式**
    + 减少RT的内存占用开销
    + 比如RenderTextureFormat.RGB111110Float(但是一些机器不支持)
<br/>

10. ## **RT Linear**
    + https://docs.unity3d.com/es/2018.2/ScriptReference/RenderTextureReadWrite.html
    + RenderTextureReadWrite.Linear
    + 这个API可以避免RT读取的时候SRGB->Linear , 颜色写入最后Linear->SRGB , 减少消耗
<br/>

11. ## **1个Pass多光源计算**
    + builtin是多个pass完成光的颜色叠加
    + SRP可以获取传入的多个光数据一个Pass就可以完成,从而提高性能
    + 可以1个主光源(有阴影)+4个附加光(无阴影)
<br/>

12. ## **Shader的uniform根据策略更新**
    + SRP Batch相关 , 减少CPU Write
<br/>

13. ## **逐相机设置参数**
<br/>

------------------------
<span id='3'/>

## **3. Project**
1. ## **Z-Pre Pass**
    + SRP Batch相关 , 减少CPU Write
<br/>
------------------------
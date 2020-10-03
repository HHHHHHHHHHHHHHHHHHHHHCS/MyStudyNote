**Unity移动游戏项目优化案例分析（上）**
=================

### 最近把UWA2020技术相关的视频看的七七八八 , 做做笔记以防遗忘.
(知乎好像不能内部页面跳转emmmm....排版还有点问题)
(可能Github比较正常: https://github.com/HHHHHHHHHHHHHHHHHHHHHCS/MyUWA2020Note/blob/main/Unity%E7%A7%BB%E5%8A%A8%E6%B8%B8%E6%88%8F%E9%A1%B9%E7%9B%AE%E4%BC%98%E5%8C%96%E6%A1%88%E4%BE%8B%E5%88%86%E6%9E%90%EF%BC%88%E4%B8%8A%EF%BC%89.md)

------------------------

[1. drawCall 和 batch 的区别](#1)<br>
[2. Batching , SRP Batcher 和 SRP Instancing](#2)<br>
[3. DrawMeshInstance VS DrawMeshInstanceIndirect](#3)<br>
[4. UIRebuild](#4)<br>
[5. UIRebatch(Canvas为单位)](#5)<br>
[6. Overdraw](#6)<br>

------------------------
<span id='1'/>

## **1. drawCall 和 batch 的区别**
### &nbsp;&nbsp; DrawCall : CPU发送渲染命令给GPU , 如:glDrawElements(OpenGL) / glDrawArrays(OpenGL) / DrawIndexedPrimitive(DX)
### &nbsp;&nbsp; Batch : CPU发送渲染的数据给GPU(CPU Write) , 如 设置顶点数据 glBufferData(OpenGL) / glBufferSubData(OpenGL) 等.
### &nbsp;&nbsp; 相关更多:https://zhuanlan.zhihu.com/p/68530142
<br/>

------------------------
<span id='2'/>

## **2. Batching , SRP Batcher 和 SRP Instancing**
* ## **Static Batching**
### &nbsp;&nbsp;条件:
1. ### 相同的材质球 , 可以不同的Mesh

### &nbsp;&nbsp;优点:
1. ### 节省顶点信息的绑定
2. ### 节省几何信息的传递
3. ### 相邻材质相同时, 节省材质的传递

### &nbsp;&nbsp;缺点:
1. ### 离线合并 , 离线包体变大(重复Mesh)
1. ### 运行时合并 , CombineMesh会造成CPU短时间峰值
3. ### 内存变大(重复Mesh)
<br/>


* ## **SRP Batcher**
### &nbsp;&nbsp;条件:
  1. ### 相同的Shader(变体一样), 可不同的Mesh

### &nbsp;&nbsp;优点:
1. ### 节省Uniform Buffer的写入操作
    + ### 按Shader 分 Batch , 预先生成Uniform Buffer
      - ### 相同shader , uniform 变量相同
      - ### PerDraw 合成一个大的Buffer
      - ### PerMaterial 格子合成一个小的Buffer
    + ### 每个Batch开始时 , 通过map(memcpy)的方式 一次性传入Uniform Buffer
    + ### Batch 内部无 CPU Write

### &nbsp;&nbsp;缺点:
1. ### Constant Buffer(CBuffer)的显存固定开销
    + ### 1024个PerDraw 384KB
    + ### 1个PerMaterial 4KB
2. ### 不支持MaterialPropertyBlock
<br/>

* ## **GPU Instancing**
### &nbsp;&nbsp;条件:
  1. ### 相同的Mesh相同的材质球

### &nbsp;&nbsp;缺点:
1. ### 可能存在负优化 (Instancing 有时候会让DrawCall变高 , 一些机器DrawCall敏感 , 所以开Instancing 需要大幅度降低DrawCall 才适用)
2. ### Instancing有时候被打乱 , 导致不完美Instancing (可以自己分组用API渲染,保证不被打乱)
<br/>

* ## 其他
1. SRP Batcher 和 Static Baching 可以兼容同时开启
2. 优先级建议 SRP Batcher / Static Batching > GPU Instancing > Dynamic Batching
3. 适用情况
    + Static + SRP Batcher : 主城, 副本建筑
    + SRP Batcher Only: 种类繁多的植被
    + GPU Instancing: 种类单一的植被
    + Dynamic Batching: UI , 粒子 , Sprite 等
<br/>

------------------------
<span id='3'/>

## **3. DrawMeshInstance VS DrawMeshInstanceIndirect**
* ## **单次上限**
  ### DrawMeshInstance : 128 / 256 / 512 (不同平台)
  ### DrawMeshInstanceIndirect : 无
* ## **API兼容版本**
  ### DrawMeshInstance : GLES 3.0
  ### DrawMeshInstanceIndirect : GLES 3.1(Shader Model 4.5)
* ## **Culling**
  ### DrawMeshInstance : C# Math Culling 和 Unity CPU CullingGroup
  + C# MathCulling
    - https://docs.unity3d.com/ScriptReference/GeometryUtility.CalculateFrustumPlanes.html
    - https://docs.unity3d.com/ScriptReference/GeometryUtility.TestPlanesAABB.html
    - 可以提前通过 九宫格/距离 剔除一些不可见的 , 达到更好的性能
  + Unity CPU CullingGroup
    - https://docs.unity3d.com/ScriptReference/CullingGroup.html
    - https://docs.unity3d.com/2019.4/Documentation/Manual/CullingGroupAPI.html
    - https://unitycoder.com/blog/2018/10/31/find-nearby-objects-using-cullinggroup/
    - 在Camera Culling阶段之后获取结果
    - 子线程并行执行
  + 当数量过多的时候 , CullingGroup 性能比 MathCulling 要好很多
  ### DrawMeshInstanceIndirect : GPU Culling
  + GPU Culling
    - 基于ComputeBuffer/StructuredBuffer , 利用Compute Shader去执行GPU Culling
    - 直接将计算结果交给DrawMeshInstancedIndirect
* ## **耗时**
  ### DrawMeshInstance+CullingGroup 相对于 DrawMeshInstanceIndirect+GPU Culling , DrawCall 变多(数量限制) , CPU耗时高 , GPU耗时低 , 总耗时在不同设备不一样
<br/>

------------------------
<span id='4'/>

## **4. UIRebuild**
* ## **Graphics.Rebuild(顶点修改)**
  ### 性能瓶颈环境
    + 血条
    + 飘字
    + 技能遮罩
  ### 解决办法
    + 降低刷新的频率
<br/>
 
* ## **LayoutRebuilder.Rebuild(Layout组件)**
  ### 性能瓶颈环境
    + 子物体修改时 , 会标记父节点的Layout通知修改
    + Layout修改时 , 会标记Layout的父节点的Layout通知修改 (递归向上)
  ### 触发的情况
    + 影响顶点位置的
      - Text:Set_Text
      - Image:Set_Image
    + 事件回调
      - OnEnable/OnDisable
      - OnRectTrasnformDimensionsChange
      - OnTrasnformParentChanged
      - OnDidApplyAnimationProperties
  ### 解决办法
    + 避免LayoutGroup的嵌套
    + 如果只是为了第一次的自动排序的,可以在显示之后禁用相关的组件
<br/>

* ## **CullRegistry.Cull(RectMask2D裁剪)**
  ### 触发的情况
    + 每帧遍历底下的元素进行裁剪
    + 有新的元素被加进来
  ### 解决办法
    + 性能消耗不大 , 可以不用专门关注
    + 减少底下节点的数量(几十个内没有大问题)
    + 保持节点没有改变减
<br/>

* ## **跟UWA无关 UI相关文章**
  ### 中文 https://blog.csdn.net/gaojinjingg/article/details/103565840
  ### 英文 https://learn.unity.com/tutorial/optimizing-unity-ui?language=en
<br/>

------------------------
<span id='5'/>

## **5. UIRebatch(Canvas为单位)**
* ## **触发的情况**
  ### Canvas.BuildBatch
  <br/>
* ## **解决办法**
  ### Canvs动静分离
  ### Shader动画(代价很小)
    + 用RawImage能拿到正确UV , Sprite不一定可以拿到正确的UV
    + uv-0.5 = 离中心的方向
    + 制作平移和缩放等的效果
<br/>

------------------------
<span id='6'/>

## **6. Overdraw**
 ### &nbsp;&nbsp; Overdraw 指同一像素被重复渲染的次数 , 当被重复渲染的像素过多的时 或 重复的次数过多时候 , 则造成性能浪费.
 ### &nbsp;&nbsp; 一个像素被重复n次 光栅化 , fragment , 输出合并 . 这些都会占用 GPU像素填充率 , ALU运算 , 读取贴图的带宽.
 ### &nbsp;&nbsp; https://zhuanlan.zhihu.com/p/76562327

* ## **全屏界面与场景的叠加**
  ### 关闭场景相机的渲染
<br/>

* ## **半屏界面与背景的叠加**
  ### 降低场景的分辨率(需要把场景绘制到RT上)
  ### 降低场景相机的更新频率(需要把场景绘制到RT上)
  ### 改成Blur静态背景(需要把场景绘制到RT上)
<br/>

* ## **全透明点击区域**
  ### empty4raycast(不建议 , 参考钱康来的文章 , 老版本下用且有Overdraw)
  ### CullTransparentMesh(新版本 , Alpha 为0 的时候则无Overdraw)
<br/>

* ## **大面积Mask组件**
  ### Mask有两层Overdraw
  ### 子节点的数量始终时,改为RectMask2D, 切裁剪区域外无Overdraw
  ### 不过还是要观察一下CullingRegister.Cull(Canvas.SendWillRenderCanvas中) , 这两个组件的性能比较
<br/>

* ## **大面积透明元素**
  ### Sprite多边形模式取出顶点,再塞入UI使用(不建议 , 参考钱康来文章 , 老版本使用)
  ### Sprite:Tight模式 , Quad Mesh 变成了多边形Mesh , 但是此时只是用于Sprite2D 并不是UGUI
  ### Image: Use Sprite Mesh , 配合上面的Sprite Tight 来完成UGUI Overdraw减少
<br/>

* ## **边框元素的FillCenter**
  ### 九宫格的时候(Image Type 为 Sliced) 去掉 FillCenter
<br/>

------------------------
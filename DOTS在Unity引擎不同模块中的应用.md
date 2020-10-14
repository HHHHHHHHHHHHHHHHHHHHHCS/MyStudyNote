**DOTS在Unity引擎不同模块中的应用**
=================

### emmmmmmmmmmmmmmm这个视频看完感觉像是DOTS的简介
### 推荐一手ECS大手子:https://www.zhihu.com/people/benzx-84/posts
(Github正常排版: [DOTS在Unity引擎不同模块中的应用](TODO:))

------------------------

[1. drawCall 和 batch 的区别](#1)<br>
[2. Batching , SRP Batcher 和 SRP Instancing](#2)<br>
[3. DrawMeshInstance VS DrawMeshInstanceIndirect](#3)<br>
[4. UIRebuild](#4)<br>
[5. UIRebatch(Canvas为单位)](#5)<br>
[6. Overdraw](#6)<br>

------------------------
<span id='1'/>

## **简介**
* ## **DOTS(Data Oriented Technology Stack)**
  + 有啥?
    - Entity Component System(ECS)
    - C# Job System
    - Burst Compiler
  + 做啥?
    - 解决大批数据计算性能的问题
  + 要啥?
    - 关注性能
    - 面向数据思想
    - 硬件并行能力
<br/>

* ## **ECS**
  + 简介
    - 面向数据
    - 组成:Entity(id) Component(数据) System(逻辑)
    - World拥有n个Entity,Entity拥有n个Component,System处理Component
  + 面向对象(非ECS)
    - 数据散放于内存中.(减慢缓存写入速度)
    - 多余数据一起加载.(占用缓存空间)
  + ECS
    - Archetype:不同Components的特定组合
    - 相同的Archetype的数据,在内存中,会连续存放于固定大小(16k)的Chunk中.(相关Component数据可以快速写入缓存)
    - Chunk中同类型的Component数据连续存放(SOA).(同类型的数据线性存储避免缓存行浪费)
  + ECS优点
    - Chunk数据连续存放布局,可以提升缓存命中
    - 内存管理不使用托管堆,避免GC
    - 快速查询entity以及获取component数组数据的效率大幅度提高,远大于GameObject.Find,GameObject.Getcomponents
<br/>

* ## **Job System**
  + CPU多线程实现方式
    - 把主线程的事情,分割成一个个Job,放入JobQueue,再由JobQueue分发到多线程上处理
  + C# Job System
    - 使用C#调用,隐藏线程调度,资源竞争等处理方式
    - 数据类型的限制,struct/blittable/非托管内存容器
<br/>

* ## **Burst**
  + 简介
    - 基于LLVM的编译器
    - 把逻辑语言转换成中间语言,再对中间语言进行优化,最后把中间语言生成目标平台的机器码
      - 如:Clang->LLVMIR->x86/ARM等
    - Unity实现了C#->.NET assembly,即逻辑语言到中间语言
  + 使用限制
    - 用于Job System和Function Pointer(FunctionPointer<T>)
    - 不能使用引用类型
    - 无法trycatch
    - 无法访问托管对象
    - 无法写入静态变量
  + 优点
    - 因为代码进行优化,所以更高效运行
    - SIMD指令优化,让数据并行处理
      - 以往A1+B1=C1,A2+B2=C2 2个指令
      - Burst 可以只用 1个指令并行
    - 运行效率比肩C++,比IL2CPP快
<br/>

------------------------
<span id='2'/>

## **2. Rendering**
* ## **ECS渲染**
  + 数据准备:位置+模型信息(Mesh+Material)
  + 调用Draw API / Hybrid Render
<br/>

* ## **Hybrid Render**
  + 通过Package Manager安装
  + 渲染System(勾选RenderMeshSystemV2):Culling,API调用
  + Entity需要挂载LocaltoWorld和RenderMesh
  + LocaltoWorld->ComponentData
    - 个体自己的数据
    - 非托管chunk内存布局
      - IComponentData
        - struct类型
        - 使用blittabl变量,不能引用托管类型
        - Managed IComponentData(引用类型用)
          - Class类型,不能使用Burst,Job
  + RenderMesh->SharedComponentData
    - 同chunk的Entity共同关联数据
    - chunk之外由SharedComponentManager进行管理
      - 可以使用引用类型
    - 数据可以共享,对entity进行chunk进行分组
      - 降低Set pass call,优化GPU Instancing
<br/>

* ## **Draw API**
  + DrawMesh
  + DrawMeshInstanced
    - 移动平台大部分兼容
  + DrawMeshInstanceIndirect
    - 功能完善,移动平台不一定兼容
  + BatchRendererGroup
    - https://zhuanlan.zhihu.com/p/105616808?utm_source=qq
    - Unity2019新增
    - 通用渲染类,兼容ECS,Builtin,SRP , 当前版本的Hybrid Render也用这个API
    - 渲染API的高层封装
    - 方便用户使用自己的culling方法
      - var xx = new BatchRendererGroup(MyCullingMethod)
<br/>

* ## **对比**
  + BatchRendererGroup  VS  DrawMeshInstanced
    - BatchRendererGroup有可以传入culling放
    - DrawMeshInstanced没有culling,需要自己culling完成把结果传入渲染
  + ECS  VS  GameObject(无Instance)
    - ECS 的 Set pass call 更少,因为GameObject的渲染时,材质被打乱,Shader切换导致
    - Batches 一样 , 因为大家都没有合批
    - ECS 的 CPU耗时更低 , FPS更高
  + EC  VS  GameObject(有Instance)
    - Batches 减少,GameObject的渲染,材质球合批被打乱导致
    - ECS 的 CPU耗时更低 , FPS更高

  + ECS VS GameObject
    - ECS提升渲染效率
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
  ### 九宫格的时候(Image Type 为 Sliced/Tiled) 去掉 FillCenter
<br/>

------------------------
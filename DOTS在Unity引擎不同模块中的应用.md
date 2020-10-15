**DOTS在Unity引擎不同模块中的应用**
=================

### emmmmmmmmmmmmmmm这个视频看完感觉像是DOTS的简介
### 推荐一手ECS大手子:https://www.zhihu.com/people/benzx-84/posts
(Github正常排版: [DOTS在Unity引擎不同模块中的应用](https://github.com/HHHHHHHHHHHHHHHHHHHHHCS/MyUWA2020Note/blob/main/DOTS%E5%9C%A8Unity%E5%BC%95%E6%93%8E%E4%B8%8D%E5%90%8C%E6%A8%A1%E5%9D%97%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8.md))

------------------------

[1. 简介](#1)<br>
[2. 渲染](#2)<br>
[3. 转换](#3)<br>
[4. 蒙皮动画](#4)<br>
[5. 物理](#5)<br>
[6. 场景](#6)<br>
[7. UI](#7)<br>
[8. 建议](#8)<br>


------------------------
<span id='1'/>

## **1. 简介**
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

## **2. 渲染**
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
  + ECS  VS  GameObject
    - ECS提升渲染效率
    - 避免GameObject管理开销(场景管理,逐物体方法的调用)
    - 属性更新适合Job加速运算
      - 如:让一堆cube向上移动
      - GameObject + 25k Cube > 10FPS
      - ECS + 25k Cube > 30FPS
      - ECS + Job + 50K Cube >= 50FPS
      - ECS + Job + Burst + 50K Cube = 60 FPS
      - 主线程耗时大大减少了,因为位置更新时,主线程出现了计算瓶颈
<br/>

------------------------
<span id='3'/>

## **3. 转换**
* ## **问题**
  + GameObject全部转换ECS任务艰巨
    - MonoBehaviour组件逻辑转换System繁琐
    - 使用了复杂的渲染管线
    - 使用了第三方插件难以转换
<br/>

* ## **自动转换**
  + 目的
    - 设计阶段保留Unity传统模式
    - Runtime阶段使用ECS高效处理方式
  + 方法
    - 渲染可能需要Hybrid Renderer
    - 挂载自动转换脚本 ConvertToEntity
      - Transform -> LocalToWorld
      - MeshRender -> RenderMesh
    - 转换自定义MonoBehaviour组件
      - 转移逻辑到System
      - 自定义数据转换
        - GameObjectConversionSystem
        - IConverGameObjectToEntity
        - IDeclareReferencedPrefabs
<br/>

* ## **DOTS+GameObject混合使用**
  + 目的
    - ECS/Job System负责部分逻辑运算,使用GameObject进行渲染
    - 可以继续使用原来的渲染管线
    - 之前的MonoBehaviour继续有效
  + 举个粒子:ECS更新GameObject位置信息
    - 挂载ConvertToEnity脚本->选择Coversion Mode->Convert And Inject GameObject让LocalToWorld和Transform同时拥有
    - 方式一 : 直接在System中获取Transform组件
      - ForEach(Transform).WithoutBurst().Run()
    - 方式二 : Job中更新Entity位置数据后,同步至GameObject
      - 需要给entity添加CopyTransformToGameObject
      - EntityManager.AddComponentData(entity,new CopyTransformGameObject())
    - 方式三 : 使用IJobSystem
      - 使用IJobParallelForTransform 和 TransformAccess,只针对Transform
      - 可以用BurstCompile
      - 可以多线程更新transform信息,相同Root共线程
      - 不需要ECS的概念,改造简便
    - 如 10K Cubes + 位移
      - 主要耗时都在主线程上,ECS+Job使用了多线程缓解了压力

      | 老做法 | ECS Injection(main thread) | ECS Injection(Job) | IJobParallelForTransform |
      | :----: | :----: | :----: | :----: |
      | 20FPS | 25FPS | 30FPS | 33FPS |

    - 如 35K Cubes , MI9 Pro

      | 方式 | 帧率 | 备注 |
      | :----: | :----: | :----: |
      | ECS + Job + Burst | 60FPS | GO完全转换为ECS,并使用多线程更新属性 |
      | ECS + Job | 54FPS |  |
      | ECS | 30FPS |  |
      | IJobParallelForTransform | 11FPS | 无需ECS,针对Transform |
      | ECS Injection | 10FPS | ECS与GO混合使用,利用Job多线程更新属性 |
      | Classic(老做法) | <8FPS |  |

<br/>

------------------------
<span id='4'/>

## **4. 蒙皮动画**
* ## **问题**
  + Hybrid Render / API绘制 都 不支持Skinned mesh
<br/>

* ## **解决方案**
  + Unity Animations
    - 开发中(emmmmmUnity一堆TODO的)
  + GameObject+DOTS混用
    - ECS Injection
    - IJobParallelForTransform
  + 渲染Mesh,GPU进行动画
    - Vertex Animation
    - Geometry Shader 传入VerticesBuffer(Unity的SKinedMesh和原神都这么干)(https://zhuanlan.zhihu.com/p/126294753)
      - 需要DX10(Stream Out)或OpenGL ES 3.0(Transform Feedback) (https://www.zhihu.com/question/67301295/answer/251750311)
    - GPU Skinning
<br/>

* ## **GPU Skinning + Instancing**
  + 将动画信息写入纹理
  + 运行时在Shader中采样纹理,进行GPU Skinning
  + GPU Animation
    - https://blog.uwa4d.com/archives/UWALab_GPUAnimation.html
<br/>

* ## **ECS + GPU Skinning + Instancing**
  + 烘焙动画纹理
  + 运行时ECS多线程更新位置及其其他角色信息
  + 调用DrawMeshInstanced/DrawMeshInstancedIndirect进行渲染
  + 渲染时候用GPU Animation完成动画播放
<br/>


* ## **混合使用方案**
  + 子弹等->ECS
  + 玩家角色->GameObject+ECS Injection
  + 小兵->ECS+GPU Skinning+Instancing
<br/>

------------------------
<span id='5'/>

## **5. 物理**
* ## **Unity Physics/Havok Physics**
  + 相同的数据协议,Editor设置,切换方便
  + Unity Physics
    - C#开源
    - 扩展性强
    - 不依赖缓存
    - 效率相对慢,但是比原生快
  + Havok Physics 
    - 运算精确
    - 缓存策略提升性能
    - 效率相对快
    - UnityPro用户订阅收费,但是新版本PackageManager好像免费
  + 如 20K Cubes
    - GameObject FPS:8
    - Unity Physics FPS:50
    - Havok Physics FPS:60
<br/>

* ## **物理动画**
  + 头发布料适合ECS/Job加速
  + Automatic Dynamic Bone
    - https://github.com/OneYoungMean/Automatic-DynamicBone
  + UWA Blog
    - https://blog.uwa4d.com/archives/Sparkle_DynamicBone.html
<br/>

------------------------
<span id='6'/>

## **6. 场景**
* ## **SubScene**
  + https://zhuanlan.zhihu.com/p/109943463
  + 加载/卸载效率高:SubScene -> RAM
    - 二进制存储,加载直接进入内存,不需要序列化
    - 多线程加载
    - 避免同一帧内大量GameObejct的active的调用
  + 限制
    - 本地存储,不能用到AssetBundle一些地方
    - ECS,Prefab需要完全转换到ECS
  + 如 10k Trees (PC) 实例化
    - GameObject Prefab 1518ms
    - ECS Prefab 262ms
  + 如 1k Trees (Mi9 Pro) 实例化
    - GameObject Prefab 97ms
    - ECS 15ms
<br/>

------------------------
<span id='7'/>

## **7. UI**
* ## **DOTS UI**
  + DOTS UI
    - https://github.com/supron54321/DotsUI
  + DOTS UGUI
    - https://github.com/initialPrefabs/UGUIDOTS
  + ECS+Job+Burst加速网格重建
<br/>

------------------------
<span id='8'/>

## **8. 建议**
* ## **项目中使用DOTS建议**
  + 交互简单,数量多的物体尝试ECS化
    - 植物,副本建筑等静态环境物体
      - 加载/实例化
      - batch/instancing
      - 降低场景开销
    - 子弹,物理道具等交互简单的物体
      - 属性多线程更新
      - DOTS Physics
      - instancing
      - 快速查询
    - 小怪等重复动画
      - GPU Skinning + Instancing
      - 属性多线程更新
<br/>

------------------------

Emmmm,差不多都看完了,应该更新完了.
剩下的一些视频一些不方便总结(<<手中的银河>>,<<​轻量级Web3D引擎关键技术及移动网页在线可视化示范应用>>)
还有一些视频可能不感兴趣,偏美术向,偏项目管理和立项,偏项目QA测试


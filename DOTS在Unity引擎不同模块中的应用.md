**DOTS在Unity引擎不同模块中的应用**
=================

### emmmmmmmmmmmmmmm这个视频看完感觉像是DOTS的简介
### 推荐一手ECS大手子:https://www.zhihu.com/people/benzx-84/posts
(Github正常排版: [DOTS在Unity引擎不同模块中的应用](https://github.com/HHHHHHHHHHHHHHHHHHHHHCS/MyUWA2020Note/blob/main/DOTS%E5%9C%A8Unity%E5%BC%95%E6%93%8E%E4%B8%8D%E5%90%8C%E6%A8%A1%E5%9D%97%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8.md))

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

------------------------
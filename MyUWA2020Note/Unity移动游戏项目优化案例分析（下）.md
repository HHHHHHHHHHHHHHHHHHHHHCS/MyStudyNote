**Unity移动游戏项目优化案例分析（下）**
=================

(Github正常排版: [Unity移动游戏项目优化案例分析（下）](https://github.com/HHHHHHHHHHHHHHHHHHHHHCS/MyStudyNote/blob/main/MyUWA2020Note/Unity%E7%A7%BB%E5%8A%A8%E6%B8%B8%E6%88%8F%E9%A1%B9%E7%9B%AE%E4%BC%98%E5%8C%96%E6%A1%88%E4%BE%8B%E5%88%86%E6%9E%90%EF%BC%88%E4%B8%8B%EF%BC%89.md))

------------------------

[1. Shader](#1)<br>
[2. 场景加载](#2)<br>
[3. C#](#3)<br>
[4. Lua](#4)<br>
[5. ILRuntime](#5)<br>
[6. 物理](#6)<br>
[7. 动画](#7)<br>
[8. 内存](#8)<br>

------------------------
<span id='1'/>

## **1. Shader**
### &nbsp;&nbsp;**问题:**
1. ### 卡顿
2. ### ShaderLab占用内存过大

### &nbsp;&nbsp;**原因:**
1. ### Shader.Parse-->Shader加载和解析
    + 变体数控制-->Shader被编译成多份,占用内存变大
    + 缓存控制-->避免Shader多次加载卸载,比如Shader在场景包中,切换场景被卸载加载
    + 冗余控制-->同一Shader冗余在不同Bundle中被多次加载
2. ### Shader.CreateGPUProgram-->GPU对要渲染Shader的目标平台编译
    + 冗余控制
    + Shader过多-->过多的时候,会导致编译过久,卡顿.

### &nbsp;&nbsp;**解决:**
1. ### 编译过久
    + 预先Warmup Shader.WarmupAllShaders()
3. ### 变体控制
    + 可以用shader_feature 代替 multi_compile
    + 收集需要的Variants
      - Graphics Settings --> Shader Stripping
      - Shader Variants Collection(SVC)
    + 剔除不需要的Variants
      - OnProcessShader(2018之后)
3. 冗余控制
    + 打包策略
    + UWA检测
    + https://blog.uwa4d.com/archives/1577.html
4. 缓存控制
    + Asset+脚本引用+DontDestory
    + Asset+Keep Loaded Shaders Alive(Graphics Settings里)
<br/>

------------------------
<span id='2'/>

## **2. 场景加载**
* ## **Async Upload Pipeline(AUP)**
&nbsp;&nbsp; 渲染线程异步上传资源
### &nbsp;&nbsp;**条件:**
1. ### 只对纹理和Mesh生效
2. ### 要关闭Read/Write

### &nbsp;&nbsp;**策略:**
1. ### 加载场景时,让BufferSize变大(Settings->Quality)
    + 分配给上传的内存变大
2. ### 加载场景时,让TimeSlice变大(Settings->Quality)
    + 分配给上传的时间变大
<br/>


* ## **Texture Stream**
&nbsp;&nbsp; 分层加载mipmap,不完全加载就进入场景
### &nbsp;&nbsp;**条件:**
  1. ### 依赖Async Upload Pipeline(AUP)
  2. ### 需要Settings->Quality里面开启Texture Streaming
  3. ### 需要开启mipmap

### &nbsp;&nbsp;**策略:**
1. ### 加载时和运行时设置两套参数 
    + ### Memory Budget(给纹理的内存预算越少,纹理加载的mip level基本就越低)
    + ### Max Reduction(分层mipmap最大限制, 减少level越大, 图片越小)

<br/>

* ## **Mesh.Bake PhsX CollisionData**
### &nbsp;&nbsp;**问题:**
1. ### Mesh过大/复杂 , 每次进场景都需要运行时计算Collision数据 , 让加载过久
2. ### 需要开启Read/Write , 这样就不能用AUP了

### &nbsp;&nbsp;**解决:**
1. ### Prebake Collision Meshes(Settings -> Player)
    + 包体大小上升,内存占用上升
2. ### 使用简化Mesh或者LOD作为碰撞体
<br/>

* ## Shader.Parse
&nbsp;&nbsp; 看上面的[1. Shader](#1)<br>
<br/>

------------------------
<span id='3'/>

## **3. C#**
* ## **实例化/激活**
1. 比如动画组件的激活/禁用
<br/>

* ## **Incremental GC**
1. 2019可以在Player->Use incremental GC 开关增量GC
2. GarbageCollector.GCMode == GarbageCollector.Mode.Disabled/Enabled
    + 可以开关GC , 比如在战斗时候关掉GC回收 , 但是要注意泄漏 ( WebGL 和 Editor 不生效)
3. VSync/Application.targetFrameRate 限制帧数
    + 很多GC的产生都是在Update里面 , 帧数下去了 , 则GC就产生就减少了
    + 因为帧数限制 增量GC 会把GC处理分配到要等待的时间里面
4. GarbageCollector.incrementalTimeSliceNanosecords(逐帧花费多少时间在GC上面)
<br/>

* ## **堆内存累积分配**
1. Boxing--dnspy看编译
    + 拆/装箱
    + 新建数组
    + 新建对象
2. ZString
    + 堆内存分配明显变低
    + CPU耗时变高
<br/>

* ## **内存驻留(泄漏)**
1. Lua索引引用导致的Mono泄漏 -- Unity释放,Lua抓着,导致中间层的Mono内存驻留了
2. C#引用 -- 如在Update里不规范使用C#代码 , 导致堆内存越来越多
3. Texture.GetPixels/WWW.bytes Bug -- 一次分配较大的数据可能会概率导致泄漏 ,  用GetPixels32代替 , 可以用C++代码下载或别的API下载
<br/>

------------------------
<span id='4'/>

## **4. Lua**
1. **Lua到C#的调用次数**
    + 过多的Lua->C#->Lua穿梭会导致耗时 , 可以C#写一个大方法 , 让Lua一次性去调用 , 然后一次性返回值
2. ## **Lua函数耗时**
    + Lua的代码性能 , 不如C# ,所以一些性能瓶颈方法可以写到C#里面
3. ## **LuaGC(Incremental)**
    + https://blog.csdn.net/dingqinghui/article/details/85323957
    + Lua_GCSETPAUSE
    + Lua_GCSETPSTEPMUL
4. ## **临时内存**
    + Vector3 , Color 等
<br/>

------------------------
<span id='5'/>

## **5. ILRuntime**
1. **解译语言,速度还是差20~100倍,可将耗时的方法放入原生语言**
2. **动态更新DLL打Relase版本 + DISABLE_ILRUNTIME_DEBUG 否则性能会下降**
3. **Android可平台特殊处理**
    + 通过Assembly.Load动态加载DLL
    + 通过GetType获取类型
    + 通过AddComponent挂载组件执行逻辑
4. **堆内存**
    + 会有缓存让内存增加
      - 会缓存中间变量,临时变量,执行过的方法等
      - 但是缓存有上限.
      - 比如配置表用ILRuntime的内存比预想的内存多
     + PDB占用
       - 移除PDB文件的加载
       - 控制热更新的DLL代码
<br/>

------------------------
<span id='6'/>

## **6. 物理**
1. **Auto Simulate 自动物理模拟**
    + 在Settings->Auto Simulation开关 
    + 默认开启,如果关闭则Rigibody.OnTrigger等物理方法就无法使用了
    + 如果碰撞很少,则可以关闭,自己可以通过距离模拟进行检测
    + 但是可以手动调用 Physics.Simulate 即模拟一帧触发物理
2. **Auto Sync Transforms 自动更新物理世界坐标**
    + 在Settings->Auto Sync Transforms开关 
    + 不勾选(默认),物体Trasnform发生改变,在下一次物理Update()前,碰撞体属性不会改变.
    + 勾选,物体Trasnform发生改变,碰撞体属性立即更新.同一帧数内频繁更新Trasnform则会有性能消耗.
    + 如果想在同一帧数改变位置且进行物理检测, 则可以用Physics.SyncTransform() 立即更新物理信息
<br/>

------------------------
<span id='7'/>

## **7. 动画**
1. **Animator.Initialize**
    + 在每次Enable的时候会调用一次 , 有性能消耗
    + 可以只禁用Render , 不禁用Animator
    + 新版本Animator.keepAnimatorControllerStateOnDisable
2. **AnyState**
    + AnyState连线过多的时候,导致检测过多,耗时过久
<br/>

------------------------
<span id='8'/>

## **8. 内存**
1. **GfxDriver**
    + 粒子系统Mesh过大,造成内存占用过多,最终VBO = Mesh内存 * Mesh个数
    + SRP Batcher , 1024个材质球约384KB , 1个材质球实例化约4KB
2. **Audio**
    + AudioClipLoadType.DecompressOnload
      - 从磁盘读取就全部解压到内存中
      - 多AudioSource使用同一份音频时,只有一份音频内存
      - CPU开销比较低 , 因为没有动态解压缩
      - 适合短音频 , 多AudioSource , 小文件(大文件勿开 , 因为音频压缩比为10倍 , ADPCM 编码约为 3.5 倍)
    + AudioClipLoadType.Streaming
      - 从磁盘读取时音频内存小 , 边播放 边从磁盘中逐渐读取加载到内存中.
      - 如果多AudioSource播放 , 因为播放的区间不同 , 则要加载多份音频区间到内存中
      - 即使没有加载任何音频数据，也有大约 200KB 的内存占用
      - 适合长音频 , 单AudioSource , 大文件
<br/>

------------------------
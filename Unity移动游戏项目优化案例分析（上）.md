Unity移动游戏项目优化案例分析（上）
=================
<br/>

------------------------
## 1. drawCall 和 batch 的区别
### &ensp;&ensp; DrawCall : CPU发送渲染命令给GPU , 如:glDrawElements(OpenGL) / glDrawArrays(OpenGL) / DrawIndexedPrimitive(DX)
### &ensp;&ensp; Batch : CPU发送渲染的数据给GPU(CPU Write) , 如 设置顶点数据 glBufferData(OpenGL) / glBufferSubData(OpenGL) 等.
### &ensp;&ensp; 相关更多:https://zhuanlan.zhihu.com/p/68530142
<br/>

------------------------
## 2. Batching , Instancing 和 SRP Batcher
* ## Static Batching
### &ensp;&ensp;条件:
1. ### 相同的材质球 , 可以不同的Mesh
<br/>

### &ensp;&ensp;优点:
1. ### 节省顶点信息的绑定
2. ### 节省几何信息的传递
3. ### 相邻材质相同时, 节省材质的传递
<br/>

### &ensp;&ensp;缺点:
1. ### 离线合并 , 离线包体变大(重复Mesh)
1. ### 运行时合并 , CombineMesh会造成CPU短时间峰值
3. ### 内存变大(重复Mesh)
<br/>


* ## SRP Batcher
  ### 条件:
  1. ### 相同的Shader(变体一样), 可不同的Mesh
<br/>

### &ensp;&ensp;优点:
1. ### 节省Uniform Buffer的写入操作
    + ### 按Shader 分 Batch , 预先生成Uniform Buffer
      - ### 相同shader , uniform 变量相同
      - ### PerDraw 合成一个大的Buffer
      - ### PerMaterial 格子合成一个小的Buffer
    + ### 每个Batch开始时 , 通过map(memcpy)的方式 一次性传入Uniform Buffer
    + ### Batch 内部无 CPU Write
<br/>

### &ensp;&ensp;缺点:
1. ### Constant Buffer(CBuffer)的显存固定开销
    + ### 1024个PerDraw 384KB
    + ### 1个PerMaterial 4KB
2. ### 不支持MaterialPropertyBlock
<br/>

* ## 其他
1. GPU Instancing
  条件: 相同的Mesh相同的材质球
  问题:
    + 可能存在负优化 (instance 有时候会让DrawCall变高 , 一些机器DrawCall敏感)
    + 实例化有时候被打乱 , 导致不完美实例化

2. SRP Batcher 和 Static Baching 可以兼容同时开启

3. SRP Batcher / Static Batching > GPU Instancing > Dynamic Batching

4. 使用情况

  ### SRP Batcher 和 Static Baching 可以兼容同时开启 



, 比如主城的建筑 或 副本的建筑

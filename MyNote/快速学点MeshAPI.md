快速学点MeshAPI
=================

(Github正常排版: [快速学点MeshAPI][1])

-----------------

<!-- @import "[TOC]" {cmd="toc" depthFrom=1 depthTo=6 orderedList=false} -->

<!-- code_chunk_output -->

- [**0. 起因**](#-0-起因-)
- [**1. MeshDescriptor**](#-1-meshdescriptor-)

<!-- /code_chunk_output -->

-----------------

## **0. 起因**

&emsp;&emsp; 都什么年代了还在用传统Mesh API. 随着Unity版本更新, 学点新的API. (你什么档次和我用一样的API, 砸了!)

包括下面几个点, 主要参考来源都是keijiro的Gayhub.
  + MeshDescriptor
  + NativeArray + Job
  + RawData + Compute Shader
  + Combine相关
  + 序列化相关

-----------------

## **1. MeshDescriptor**

之前的写法的写法是:

设置vertices, normals. 再设置Mesh的IndexFormat为UInt32.

再设置 mesh中 索引为0的SubMesh 的 indexData(newIndices) 和 绘制模式(Triangles).

```C#

Mesh mesh = new Mesh();

mesh.vertices = newVertices;
mesh.normals = newNormals;

mesh.indexFormat = IndexFormat.UInt32
mesh.SetIndices(newIndices, MeshTopology.Triangles, 0);

```

后面出了**VertexAttributeDescriptor**, 学过OpenGL/DX之类的应该都熟悉 顶点属性描述, 可以包含位置, UV, 法线等等. [官方文档][2]

所以上面的vertex position和normal布局可以写成下面这样, 注意这里还没有填充数据. 

然后再补充Index Buffer属性, 即Index Buffer Count 和 Format.

```C#

Mesh mesh = new Mesh();

mesh.SetVertexBufferParams(verticesCount, new VertexAttributeDescriptor(VertexAttribute.Position, stream: 0)
, new VertexAttributeDescriptor(VertexAttribute.Normal, stream: 1));

mesh.SetIndexBufferParams(indicesCount, IndexFormat.UInt32);

```

然后进行数据填充, 这里省略掉了数据设置.

直接用 **SetVertexBufferData** 和 **SetIndexBufferData** 设置BufferData.

**MeshUpdateFlags**, 可以告诉 Unity 当Mesh数据更新的时候你别做一些事情. 比如 **DontRecalculateBounds** 不要自动生存包围盒, **DontValidateIndices** 不要检查Index索引(可能存在越界). 详见[官方文档][3].

```C#

var vertexPos = new NativeArray<Vector3>(verticesCount, Allocator.Temp);
var vertexNor = new NativeArray<Vector3>(verticesCount, Allocator.Temp);

//省略了数据填充

mesh.SetVertexBufferData(vertexPos, 0, 0, vertexPos.Length, 0, MeshUpdateFlags.DontRecalculateBounds);
mesh.SetVertexBufferData(vertexNor, 0, 0, vertexNor.Length, 1, MeshUpdateFlags.DontRecalculateBounds);


vertexPos.Dispose();
vertexNor.Dispose();

var indicesBuffer = new NativeArray<int>(verticesCount, Allocator.Temp);

//省略了数据填充

mesh.SetIndexBufferData(indicesBuffer, 0, 0, indicesBuffer.Length, MeshUpdateFlags.DontRecalculateBounds | MeshUpdateFlags.DontValidateIndices);

indicesBuffer.Dispose();

```

接着就是设置SubMesh.

同时因为上面让其不要自动生成包围盒, 渲染的时候存在Culling问题. 所以还可以指定一下.

```C++

var subMesh = new SubMeshDescriptor(0, indicesCount, MeshTopology.Triangles);
mesh.SetSubMesh(0, subMesh);

subMesh.bounds = new Bounds(Vector3.zero, new Vector3(10, 10, 10));
mesh.bounds = subMesh.bounds;

```

甚至还可以调用 **mesh.UploadMeshData(true)** , 立即把修改后的Mesh Data 发给 渲染API. **markNoLongerReadable** 如果为true, mesh将卸载掉脚本层的数据拷贝, 脚本层不能对mesh数据做读取, 跟Mesh的ReadOnly很像. [官方文档][4]

-----------------

[1]:https://github.com/HHHHHHHHHHHHHHHHHHHHHCS/MyStudyNote/tree/main/MyNote
[2]:https://docs.unity3d.com/2022.2/Documentation/ScriptReference/Rendering.VertexAttributeDescriptor.html
[3]:https://docs.unity.cn/ScriptReference/Rendering.MeshUpdateFlags.html
[4]:https://docs.unity.cn/ScriptReference/Rendering.MeshUpdateFlags.html
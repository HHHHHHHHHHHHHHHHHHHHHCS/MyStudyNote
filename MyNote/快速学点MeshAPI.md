快速学点MeshAPI
=================

(Github正常排版: [快速学点MeshAPI][1])

-----------------

<!-- @import "[TOC]" {cmd="toc" depthFrom=1 depthTo=6 orderedList=false} -->

<!-- code_chunk_output -->

- [**0. 起因**](#0-起因)
- [**1. MeshDescriptor**](#1-meshdescriptor)
- [**2. NativeArray + Job**](#2-nativearray--job)
  - [**2.1 老方法**](#21-老方法)
  - [**2.1.1 基础代码**](#211-基础代码)
  - [**2.1.2 创建Mesh**](#212-创建mesh)
  - [**2.1.3 动起来**](#213-动起来)
  - [**2.2 Job**](#22-job)
  - [**2.2.1 Create Mesh**](#221-create-mesh)
  - [**2.2.1 创建Mesh**](#221-创建mesh)
  - [**2.2.3 更新MeshPos**](#223-更新meshpos)
  - [**2.2.3 更新MeshNormal**](#223-更新meshnormal)
- [**2.3. GPU**](#23-gpu)
  - [**2.3.1 Create Mesh**](#231-create-mesh)
  - [**2.3.2 绑定GPU资源**](#232-绑定gpu资源)

<!-- /code_chunk_output -->

-----------------

## **0. 起因**

&emsp;&emsp; 都什么年代了还在用传统Mesh API. 随着Unity版本更新, 学点新的API. (你什么档次和我用一样的API, 砸了!)

包括下面几个点, 主要参考来源[代码仓库][5]. 当然也可以看看keijiro的Gayhub, 里面也有很多新奇的东西.
  + MeshDescriptor
  + NativeArray + Job
  + GraphicsBuffer.Target.Raw + RWByteAddressBuffer
  + Combine相关
  + 序列化相关

建议使用2021+的版本, 因为RawData需要.

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

```C#

var subMesh = new SubMeshDescriptor(0, indicesCount, MeshTopology.Triangles);
subMesh.bounds = new Bounds(Vector3.zero, new Vector3(10, 10, 10));
mesh.SetSubMesh(0, subMesh);
mesh.bounds = subMesh.bounds;

```

甚至还可以调用 **mesh.UploadMeshData(true)** , 立即把修改后的Mesh Data 发给 渲染API. **markNoLongerReadable** 如果为true, mesh将卸载掉脚本层的数据拷贝, 但是脚本层之后不能对mesh数据做读取, 跟Mesh的ReadOnly很像. [官方文档][4]

-----------------

## **2. NativeArray + Job**

Talk is cheap, show me your code!

### **2.1 老方法**

先来写一个以前版本的写法. 写完大概就是下图这样.

![MeshAPI_00](Images/MeshAPI_00.png)

新建一个Plane, 命名为Water. 然后以Water为父节点, 随便摆放几个Cube.

![MeshAPI_00](Images/MeshAPI_01.jpg)

![MeshAPI_00](Images/MeshAPI_02.jpg)

### **2.1.1 基础代码**

新建个C# **WaterMesh.cs**, 添加 **RequireComponent**, 并且拖拽给Water.

```C#

using UnityEngine;
using UnityEngine.Rendering;

[RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
public class WaterMesh : MonoBehaviour
{
}

```

首先需要数据, 这个Plane需要多大, 细分多少个点.

然后直接补充方法, 在 **OnEnable** 中创建 Mesh, **OnDisable** 中销毁Mesh.

因为要考虑到后面别的MeshAPI测试, 所以写了点代码结构.

```C#

public float widthSize = 10;
public float heightSize = 10;
[Min(2)] public int widthPoints = 100;
[Min(2)] public int heightPoints = 100;

private Mesh waterMesh;
private Vector3[] vertices;

private void OnEnable()
{
	CreateMesh();
}

private void OnDisable()
{
	if (waterMesh != null)
	{
		CoreUtils.Destroy(waterMesh);
	}
}

private void CreateMesh()
{
	waterMesh = CreateMesh_Old();
	GetComponent<MeshFilter>().sharedMesh = waterMesh;
}

private Mesh CreateMesh_Old()
{
	//TODO:
}

```

### **2.1.2 创建Mesh**

完善 **CreateMesh_Old** 方法.

不多赘述, 注意三角绘制顺序就行.

当老模式的时候, 用Unity自带的方法 **RecalculateNormals** 去重建Normal比较快.

```C#

private Mesh CreateMesh_Old()
{
	var mesh = new Mesh();

	mesh.name = "WaterMesh_Old";
	mesh.indexFormat = IndexFormat.UInt32;

	vertices = new Vector3[widthPoints * heightPoints];

	Vector3 startPos = new Vector3(-widthSize * 0.5f, 0, -heightSize * 0.5f);
	float stepOffsetX = widthSize / (widthPoints - 1);
	float stepOffsetZ = heightSize / (heightPoints - 1);

	for (int y = 0; y < heightPoints; y++)
	{
		for (int x = 0; x < widthPoints; x++)
		{
			vertices[y * widthPoints + x] = startPos + new Vector3(x * stepOffsetX, 0, y * stepOffsetZ);
		}
	}

	int row = heightPoints - 1;
	int column = widthPoints - 1;
	int[] indices = new int[column * row * 6];
	int idxStart = 0;

	for (int y = 0; y < row; y++)
	{
		for (int x = 0; x < column; x++, idxStart += 6)
		{
			int startVert = y * widthPoints + x;
			indices[idxStart + 0] = indices[idxStart + 3] = startVert;
			indices[idxStart + 1] = indices[idxStart + 5] = startVert + widthPoints + 1;
			indices[idxStart + 2] = startVert + 1;
			indices[idxStart + 4] = startVert + widthPoints;
		}
	}

	mesh.SetVertices(vertices);
	mesh.SetIndices(indices, MeshTopology.Triangles, 0);
	mesh.bounds = new Bounds(Vector3.zero, new Vector3(widthSize, float.Epsilon, heightSize));
	mesh.RecalculateNormals();

	return mesh;
}

```

### **2.1.3 动起来**

接着让Water Mesh动起来.

那么先要获取目标点(即cubes), 可以直接偷懒用Linq写. 添加属性Transform[] cubes, 然后直接用Linq Select. 注意这时候Cube的父节点要为Water.

```C#

public class WaterMesh : MonoBehaviour
{
	...
	private Vector3[] vertices;

	private Transform[] cubes;

	private void OnEnable()
	{
		cubes = transform.Cast<Transform>().Select(x => x.transform).ToArray();
		CreateMesh();
	}
}

```

添加UpdateMesh相关的属性和方法.

添加 水的波动周期 **waveFrequency** , 周期时间 **localTime**.

更新Mesh相关的三个方法 **Update** , **UpdateMesh** 和 **UpdateMesh_Old** .

```C#

public class WaterMesh : MonoBehaviour
{
	...
	[Min(2)] public int heightPoints = 100;
	public float waveFrequency = 2.0f;

	...

	private Transform[] cubes;
	private float localTime;

	...

	private void OnDisable()
	{
		...
	}

	private void Update()
	{
		UpdateMesh();
	}

	private void CreateMesh()
	{
		...
	}

	private void UpdateMesh()
	{
		localTime = waveFrequency * Time.time;
		UpdateMesh_Old();
	}

	private Mesh CreateMesh_Old()
	{
		...
	}

	private void UpdateMesh_Old()
	{
		//TODO:
	}
}

```

完善 **UpdateMesh_Old** 方法.

波浪的y其实就是 **sin(dist * 12.0f - time) / (dist * 20 + 10)** , 再遍历cube做叠加.

```C#

private void UpdateMesh_Old()
{
	for (int i = 0; i < vertices.Length; i++)
	{
		var p = vertices[i];
		var y = 0.0f;
		foreach (var cube in cubes)
		{
			Vector3 cubePos = cube.transform.position;
			var p1 = new Vector2(p.x, p.z);
			var p2 = new Vector2(cubePos.x, cubePos.z);
			var dist = Vector2.Distance(p1, p2);
			y += Mathf.Sin(dist * 12.0f - localTime) / (dist * 20 + 10);
		}

		p.y = y;
		vertices[i] = p;
	}

	waterMesh.SetVertices(vertices);
	waterMesh.RecalculateNormals();
}

```

### **2.2 Job**

改成Job的模式去更新.

### **2.2.1 Create Mesh**

创建enum **MeshMode** 和变量 **meshMode** 用于走哪个API.

同时修改 **CreateMesh** 和 **UpdateMesh** 方法, 并且创建方法 **CreateMesh_Job** 和 **UpdateMesh_Job** .


```C#

	public class WaterMesh : MonoBehaviour
	{
		public enum MeshMode
		{
			OldMethod,
			Job,
			GPU,
		}

		public MeshMode meshMode = MeshMode.Job;
		public float widthSize = 10;
		...

		private void CreateMesh()
		{
			switch (meshMode)
			{
				case MeshMode.OldMethod:
					waterMesh = CreateMesh_Old();
					break;
				case MeshMode.Job:
					waterMesh = CreateMesh_Job();
					break;
				case MeshMode.GPU:
					//TODO:
					break;
			}

			GetComponent<MeshFilter>().sharedMesh = waterMesh;
		}

		private void UpdateMesh()
		{
			localTime = waveFrequency * Time.time;
			switch (meshMode)
			{
				case MeshMode.OldMethod:
					UpdateMesh_Old();
					break;
				case MeshMode.Job:
					UpdateMesh_Job();
					break;
				case MeshMode.GPU:
					//TODO:
					break;
			}
		}

		...

		private Mesh CreateMesh_Job()
		{
			//TODO:Create
		}

		private void UpdateMesh_Job()
		{
			//TODO:Update
		}
	}

```

### **2.2.1 创建Mesh**

这种创建方法的效率没有第一种快, 老方法是0.9ms, Job创建是2.8ms. 但是后面Update Mesh的时候速度就是云泥之别了. 

创建NativeArray<float3> vertexArray, normalArray. 这里用Job去更新Normal, 一是用来对比Unity自带生成Normal的速度, 二是方便后面用GPU. 因为申请的是 **Allocator.Persistent** 的, 所以要Dispose.

再用上面说的 **VertexBuffer** , **VertexDescriptor** 去创建Mesh. 默认normal朝上, 后面Update再修改.

```C#

...

private Vector3[] vertices;
private NativeArray<float3> vertexArray;
private NativeArray<float3> normalArray;

private void OnDisable()
{
	...
	if (vertexArray.IsCreated)
	{
		vertexArray.Dispose();
	}

	if (normalArray.IsCreated)
	{
		normalArray.Dispose();
	}
}

...

private Mesh CreateMesh_Job()
{
	int vertCount = widthPoints * heightPoints;
	var mesh = new Mesh();
	mesh.name = "WaterMesh_Job";
	mesh.SetVertexBufferParams(vertCount, new VertexAttributeDescriptor(VertexAttribute.Position, stream: 0)
		, new VertexAttributeDescriptor(VertexAttribute.Normal, stream: 1));

	vertexArray = new NativeArray<float3>(widthPoints * heightPoints, Allocator.Persistent);

	float3 startPos = new float3(-widthSize * 0.5f, 0, -heightSize * 0.5f);
	float stepOffsetX = widthSize / (widthPoints - 1);
	float stepOffsetZ = heightSize / (heightPoints - 1);

	for (int y = 0; y < heightPoints; y++)
	{
		for (int x = 0; x < widthPoints; x++)
		{
			vertexArray[y * widthPoints + x] = startPos + new float3(x * stepOffsetX, 0, y * stepOffsetZ);
		}
	}

	normalArray = new NativeArray<float3>(widthPoints * heightPoints, Allocator.Persistent);

	for (int y = 0; y < heightPoints; y++)
	{
		for (int x = 0; x < widthPoints; x++)
		{
			normalArray[y * widthPoints + x] = new float3(0, 1, 0);
		}
	}

	int row = heightPoints - 1;
	int column = widthPoints - 1;
	NativeArray<int> indexArray = new NativeArray<int>(row * column * 6, Allocator.Temp);

	int idxStart = 0;

	for (int y = 0; y < row; y++)
	{
		for (int x = 0; x < column; x++, idxStart += 6)
		{
			int startVert = y * widthPoints + x;
			indexArray[idxStart + 0] = indexArray[idxStart + 3] = startVert;
			indexArray[idxStart + 1] = indexArray[idxStart + 5] = startVert + widthPoints + 1;
			indexArray[idxStart + 2] = startVert + 1;
			indexArray[idxStart + 4] = startVert + widthPoints;
		}
	}

	mesh.SetIndexBufferParams(indexArray.Length, IndexFormat.UInt32);
	mesh.SetVertexBufferData(vertexArray, 0, 0, vertexArray.Length, 0, MeshUpdateFlags.DontRecalculateBounds);
	mesh.SetVertexBufferData(normalArray, 0, 0, normalArray.Length, 1, MeshUpdateFlags.DontRecalculateBounds);
	mesh.SetIndexBufferData(indexArray, 0, 0, indexArray.Length, MeshUpdateFlags.DontRecalculateBounds | MeshUpdateFlags.DontValidateIndices);

	var subMesh = new SubMeshDescriptor(0, indexArray.Length, MeshTopology.Triangles)
	{
		bounds = new Bounds(Vector3.zero, new Vector3(widthSize, 2.0f, heightSize))
	};
	mesh.SetSubMesh(0, subMesh);
	mesh.bounds = subMesh.bounds;

	return mesh;
}

```

### **2.2.3 更新MeshPos**

之后创建Job去更新Mesh的position.y, 完善UpdateMesh_Job.

首先要获取全部cube的位置. 然后创建Job去更新数据, 最后把数据传递给Mesh.

创建Job **UpdateMeshPosJob**, 因为是要做循环任务, 所以要继承 **IJobParallelFor**. 

**NativeDisableParallelForRestriction** 可以理解为禁用对并行处理的限制, Unity对为了安全性对数据读写添加了限制. 比如当前的Job Index是1, 但是想要读取的数据的位置是100, 那么超出了安全范围, 就会报错.

记得添加 **BurstCompile** 走burst优化编译 可以加速执行.

```C#

private void UpdateMesh_Job()
{
	NativeArray<float3> cubePosArray = new NativeArray<float3>(cubes.Length, Allocator.TempJob);
	for (int i = 0; i < cubes.Length; i++)
	{
		cubePosArray[i] = cubes[i].position;
	}

	UpdateMeshPosJob posJob = new UpdateMeshPosJob()
	{
		vertices = vertexArray,
		cubePos = cubePosArray,
		time = localTime
	};
	
	posJob.Schedule(vertexArray.Length, 16).Complete();
	//TODO:change Normal
	waterMesh.SetVertexBufferData(vertexArray, 0, 0, vertexArray.Length, 0, MeshUpdateFlags.DontRecalculateBounds);
	cubePosArray.Dispose();
}

[BurstCompile]
private struct UpdateMeshPosJob : IJobParallelFor
{
	public NativeArray<float3> vertices;

	[ReadOnly, NativeDisableParallelForRestriction]
	public NativeArray<float3> cubePos;

	public float time;

	public void Execute(int index)
	{
		var p = vertices[index];
		var y = 0.0f;
		foreach (var cubePos in cubePos)
		{
			var p1 = new Vector2(p.x, p.z);
			var p2 = new Vector2(cubePos.x, cubePos.z);
			var dist = Vector2.Distance(p1, p2);
			y += Mathf.Sin(dist * 12.0f - time) / (dist * 20 + 10);
		}

		p.y = y;
		vertices[index] = p;
	}
}

```

现在虽然可以动起来了, 但是因为是统一的颜色, 没有改动Normal, 所以效果不是很明显.

### **2.2.3 更新MeshNormal**

然后再写 **UpdateJob** .

这里的算法比较简单, 直接累加Cross得到的Normal再normalize.

这里要注意 **SetVertexBufferData** . 根据上面的**SetVertexBufferParams** 的设置, position 的 stream 为 0, normal 的 stream 为1.

```C#

private void UpdateMesh_Job()
{
	...
	posJob.Schedule(vertexArray.Length, 16).Complete();

	UpdateMeshNormalJob normalJob = new UpdateMeshNormalJob()
	{
		normals = normalArray,
		vertices = vertexArray,
		columnNum = widthPoints,
		rowNum = heightPoints
	};

	normalJob.Schedule(normalArray.Length, 16).Complete();

	waterMesh.SetVertexBufferData(vertexArray, 0, 0, vertexArray.Length, 0, MeshUpdateFlags.DontRecalculateBounds);
	waterMesh.SetVertexBufferData(normalArray, 0, 0, normalArray.Length, 1, MeshUpdateFlags.DontRecalculateBounds);

	cubePosArray.Dispose();
}


[BurstCompile]
private struct UpdateMeshPosJob : IJobParallelFor
{
	...
}

[BurstCompile]
private struct UpdateMeshNormalJob : IJobParallelFor
{
	[WriteOnly] public NativeArray<float3> normals;

	[ReadOnly, NativeDisableParallelForRestriction]
	public NativeArray<float3> vertices;

	public int columnNum, rowNum;

	public void Execute(int index)
	{
		int x = index % columnNum;
		int y = index / columnNum;

		int x_l = math.max(x - 1, 0);
		int x_r = math.min(x + 1, columnNum - 1);
		int y_b = math.max(y - 1, 0);
		int y_t = math.min(y + 1, rowNum - 1);

		float3 center = vertices[index];
		float3 left = vertices[y * columnNum + x_l] - center;
		float3 right = vertices[y * columnNum + x_r] - center;
		float3 bottom = vertices[y_b * columnNum + x] - center;
		float3 top = vertices[y_t * columnNum + x] - center;

		float3 normal = math.cross(top, right);
		normal += math.cross(left, top);
		normal += math.cross(bottom, left);
		normal += math.cross(right, bottom);

		normals[index] = math.normalize(normal);
	}
}

```

老方法约25ms. Job Pos + RecalculateNormals约0.7ms. Job Pos + Job Normal约0.5ms.

数据证明用Job重算Normal比较快一点.

-----------------

## **2.3. GPU**

最后就是需要Unity2021才支持的 GPU修改顶点数据. 设置BufferTarget, 然后传入GPU, 通过RWByteAddressBuffer进行计算.

### **2.3.1 Create Mesh**

添加方法 **CreateMesh_GPU** 和 空方法 **UpdateMesh_GPU** .

CreateMesh_GPU 与 CreateMesh_Old 类似.

```C#

private Mesh CreateMesh_GPU()
{
	var mesh = new Mesh();

	mesh.name = "CreateMesh_GPU";
	mesh.indexFormat = IndexFormat.UInt32;

	var verts = new Vector3[widthPoints * heightPoints];

	Vector3 startPos = new Vector3(-widthSize * 0.5f, 0, -heightSize * 0.5f);
	float stepOffsetX = widthSize / (widthPoints - 1);
	float stepOffsetZ = heightSize / (heightPoints - 1);

	for (int y = 0; y < heightPoints; y++)
	{
		for (int x = 0; x < widthPoints; x++)
		{
			verts[y * widthPoints + x] = startPos + new Vector3(x * stepOffsetX, 0, y * stepOffsetZ);
		}
	}

	var nors = new Vector3[widthPoints * heightPoints];

	for (int i = 0; i < nors.Length; i++)
	{
		nors[i] = Vector3.up;
	}

	int row = heightPoints - 1;
	int column = widthPoints - 1;
	int[] idxs = new int[column * row * 6];
	int idxStart = 0;

	for (int y = 0; y < row; y++)
	{
		for (int x = 0; x < column; x++, idxStart += 6)
		{
			int startVert = y * widthPoints + x;
			idxs[idxStart + 0] = idxs[idxStart + 3] = startVert;
			idxs[idxStart + 1] = idxs[idxStart + 5] = startVert + widthPoints + 1;
			idxs[idxStart + 2] = startVert + 1;
			idxs[idxStart + 4] = startVert + widthPoints;
		}
	}

	mesh.SetVertices(verts);
	mesh.SetIndices(idxs, MeshTopology.Triangles, 0);
	mesh.SetNormals(nors);
	mesh.bounds = new Bounds(Vector3.zero, new Vector3(widthSize, float.Epsilon, heightSize));

	return mesh;
}

private void UpdateMesh_GPU()
{
	//TODO:
}

```

然后 在 **CreateMesh** 和 **UpdateMesh** 中分别调用上面两个方法.

```C#

private void CreateMesh()
{
	switch (meshMode)
	{
		...
		case MeshMode.GPU:
			waterMesh = CreateMesh_GPU();
			break;
	}
	...
}

private void UpdateMesh()
{
	...
	switch (meshMode)
	{
		...
		case MeshMode.GPU:
			UpdateMesh_GPU();
			break;
	}
}

```

### **2.3.2 绑定GPU资源**

**mesh.vertexBufferTarget |= GraphicsBuffer.Target.Raw**

把MeshData进行Raw标记, 即数据变成原始数据类型(RWBuffer). 少了对数据转换和对齐, 方便当作RWBuffer给Compute Shader使用. 

**为什么用 Raw Buffer,  Structured Buffer 不行吗?** 

Vertex Buffer 可以当作是 Structured Buffer, 但是在一些图形API(尤其是DX11)上不受支持. 所以这里用Raw Buffer代替.

```C#

private Mesh CreateMesh_GPU()
{
	...
	mesh.name = "CreateMesh_GPU";
	mesh.vertexBufferTarget |= GraphicsBuffer.Target.Raw;
	...
}

```

然后创建 **GraphicsBuffer** . 一个用于顶点位置, 一个用于绑定Mesh的GPU资源.

```C#
public class WaterMesh : MonoBehaviour
{
	...
	private NativeArray<float3> normalArray;

	private GraphicsBuffer gpuPositionsCB;
	private GraphicsBuffer gpuVerticesCB;
	...


	private void OnDisable()
	{
	}

```

-----------------

[1]:https://github.com/HHHHHHHHHHHHHHHHHHHHHCS/MyStudyNote/blob/main/MyNote/%E5%BF%AB%E9%80%9F%E5%AD%A6%E7%82%B9MeshAPI.md
[2]:https://docs.unity3d.com/2022.2/Documentation/ScriptReference/Rendering.VertexAttributeDescriptor.html
[3]:https://docs.unity.cn/ScriptReference/Rendering.MeshUpdateFlags.html
[4]:https://docs.unity3d.com/ScriptReference/Mesh.UploadMeshData.html
[5]:https://github.com/Unity-Technologies/MeshApiExamples
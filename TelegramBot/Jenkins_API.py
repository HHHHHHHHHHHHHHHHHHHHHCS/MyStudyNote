# 多选框不怎么支持 不建议用

from jenkins import Jenkins

username = None
api_token = None
job_name = None

jen = Jenkins(url="http://xxx.xxx.xxx.xxx:8080", username=username, password=api_token)


parameters={
	"node":"ProgramerMachine",
	"platform":"windows"
	}


print(jen.build_job(job_name, parameters))
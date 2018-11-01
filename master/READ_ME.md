## 使用说明

### master使用说明

- 启动

http://192.168.0.157:3851/master_server/start/

- 后台

http://192.168.0.157:3851/admin/

- 依赖关系查询

http://192.168.0.157:3851/master_server/program/status/parent_son/?sid=<sid>

- 调度查询

http://192.168.0.157:3851/master_server/get_cal_result/

- 调度执行

http://192.168.0.157:3851/master_server/exec_api/<sid>/

- 添加执行计划

http://192.168.0.157:3851/master_server/add_program/


### slave使用说明

http://<slave ip>:<slave 端口>/slave_server/start/
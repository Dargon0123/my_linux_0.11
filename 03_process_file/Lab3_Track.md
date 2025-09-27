[toc]



# 0、实验内容

## 要求

进程从创建(Linux下调用*fork()*)到结束的整个过程就是进程的生命期，进程在其生命期中的运行轨迹实际上表现为进程状态的多次切换，如进程创建以后会成为就绪态；当该进程被调度以后会切换到运行态；在运行的过程中如果启动一个文件读写操作，操作系统会将该进程切换到阻塞态(等待态)从而让出CPU；当文件读写完毕，操作系统会将其切换成就绪态，等待进程调度算法来调度该进程执行…… 本实验内容包括：

- 基于模板

  process.c

  编写多进程的样本程序，实现如下功能：

  - 所有子进程都并行执行，每个子进程的实际运行时间一般不超过30秒
  - 父进程向标准输出打印所有子进程的id，并在所有子进程都退出后才退出

- 在Linux 0.11上实现进程运行轨迹的跟踪

  基本任务是在内核中维护一个日志文件*/var/process.log*，把操作系统启动到系统关机过程中所有进程的运行轨迹都记录在这一log文件中

  /var/process.log

  文件的格式必须为：

  ```log
  pid	X	time
  ```

  其中：

  - pid是进程的ID
  - X可以是N，J，R，W和E中的任意一个
    - N 进程新建
    - J 进入就绪态
    - R 进入运行态
    - W 进入阻塞态
    - E 退出
  - time表示X发生的时间。这个时间不是物理时间，而是系统的滴答时间(tick)
    三个字段之间用制表符分隔
    例如：

  ```log
  12    N    1056
  12    J    1057
  4    W    1057
  12    R    1057
  13    N    1058
  13    J    1059
  14    N    1059
  14    J    1060
  15    N    1060
  15    J    1061
  12    W    1061
  15    R    1061
  15    J    1076
  14    R    1076
  14    E    1076
  ......
  ```

- 在修改过的0.11上运行样本程序，通过分析log文件，统计该程序建立的所有进程的等待时间，完成时间(周转时间)和运行时间，然后计算平均等待时间，平均完成时间和吞吐量。可以自己编写统计程序，也可以使用python脚本程序——*stat_log.py*(在[实验楼实验环境：操作系统原理与实践](https://www.shiyanlou.com/courses/115)的在线Linux实验环境*/home/teacher*目录下)——进行统计

- 修改0.11进程调度的时间片，然后再运行同样的样本程序，统计同样的时间数据，和原有的情况对比，体会不同时间片带来的差异

- 实验报告 完成实验后，在实验报告中回答如下问题：

  - 结合自己的体会，谈谈从程序设计者的角度，单进程编程和多进程编程最大的区别是什么？
  - 你是如何修改时间片的？仅针对样本程序建立的进程，在修改时间片前后，log文件的统计结果(不包括Graphic)都是什么样？结合你的修改分析一下为什么会这样变化，或者为什么没变化？

- 评分标准

  - process.c，50%
  - 日志文件成功建立，5%
  - 能向日志文件输出信息，5%
  - 5种状态都能输出，10%(每种2%)
  - 调度算法修改，10%
  - 实验报告，20%

## Linux 0.11和Ubuntu的文件交换

两个系统间的文件交换，无非就是两种方式，这里通过实验楼的环境，记录下来两种形式。

* 0.11 ---> Ubuntu

在Ubuntu运行启动，在挂载文件系统之前，需要0.11系统是未运行，两者不能同时运行。

比如这个实验需要分析的process.log文件，需要从0.11拉出来，在Ubuntu进行分析，按照下面的程序进行操作

在0.11系统退出之前，需要执行sync，确保所有的缓存数据都存盘了，在关闭0.11系统。

![image-20250924175803968](C:\Users\dar\AppData\Roaming\Typora\typora-user-images\image-20250924175803968.png)

接着，0.11系统退出之后，同样按照下面的操作，执行hdc的挂载，然后取出自己需要的文件。



* Ubuntu ---> 0.11

```c
$ cd ~/oslab/

# 启动挂载脚本
$ sudo ./mount-hdc
```

挂载之后，就可以看到对这个hdc镜像文件所对应的文件夹的内容了。和0.11的系统里面所展现的是同样的

```c
dargon@dd:~/oslab/hdc$ ls -al
总用量 186
drwxr-xr-x 10 root   root      192 4月  28  2005 .
drwxr-xr-x  8 dargon dargon   4096 9月  21 21:13 ..
drwxr-xrwx  2 root   root      880 3月  22  2004 bin
drwxr-xrwx  2 root   root      336 3月  22  2004 dev
drwxr-xrwx  2 root   root      256 9月  24  2004 etc
drwxr-xrwx  8 root   root      128 3月  22  2004 image
-rw----rw-  1 root   root   125440 4月  28  2005 Image
drwxr-xrwx  6 root   root      112 9月  24  2004 mnt
-rwx--xrwx  1 root   root    48304 9月  22  2004 shoelace
drwxr-xrwx  2 root   root       80 9月  24  2004 tmp
drwxr-xrwx 10 root   root      160 3月  30  2004 usr
drwxr-xrwx  2 root   root       48 10月 21  2061 var
```

这时候，你可以在本地ubuntu上，添加或者copy其它文件到这个路径下下面。

读写完毕，卸载这个系统

```
$ cd ~/oslab/

# 卸载
$ sudo umount hdc
```

再去启动0.11系统的时候，就可以在shell里面，看到对应的添加的文件了。

没有处理文件系统的情况下，会报出相应的错误。

![image-20250223181014002](C:\Users\dar\AppData\Roaming\Typora\typora-user-images\image-20250223181014002.png)



# 1、实验分析

## 1.1、Process.log输出

通过对kernel的各个状态的切换代码部分，添加对应的状态打印和输出到log文间，完成第一部分的内容。输出的log文件为了便于分析，一种是对应的按照正常实验细节进行展开的，另一种是带有后缀函数的，能更好的追踪进程状态切换的来源。

通过代码中的哄定义进行控制。

```c
// linux-0.11/include/linux/sched.h
#define SHOW_SRC_FUNC_ENABLE 0

#define TASK_RUNNING		0
#define TASK_INTERRUPTIBLE	1
#define TASK_UNINTERRUPTIBLE	2
#define TASK_ZOMBIE		3
#define TASK_STOPPED		4
```

正常进程跟踪打印

```c
1	N	48 // 进程1被fork()出来，进程0是内核进程，不是fork出来，是系统内核初始化创建的第一个进程，跳到main函数就开始执行的，负责给系统做一系列的初始化工作，并且创建进程1(init进程)，而进程1，随后会创建其它用户进程。统一使用P_x-->进程_x
1	J	48 // 同一个10ms内，进入就绪队列
0	J	48 // P0通过sys_pause进入就绪队列，让出CPU
1	R	48 // P1开始正式运行，通过schedule被调度到
2	N	49 // P1 fork()出P2
2	J	49 // P2 添加对应ready_list
1	W	49 // P1在init里面调用wait，进入wait状态
2	R	49 // P1在wait之后，调schedule切换到P2 运行
3	N	63 // P2 通过execve() 建立P3，并加入ready_list里面
3	J	64
2	J	64 // P2 让出CPU，
3	R	64 // P3 开始运行
3	W	68 // P3 开始wait？
2	R	68 // P2 拿到cpu 运行，
2	E	73 // P2 执行 _exit(2);
1	J	73 // P1 wait-->就绪
1	R	73 // P1 开始运行
4	N	74 // P1 fork出 P4 shell进程
4	J	74
1	W	74 // P1 调用wait进入wait
4	R	74 // P4 拿到cpu，运行
5	N	106
5	J	106
4	W	107
5	R	107
4	J	109
5	E	109 // P5 退出
```

显示函数来源的打印输出

```c
1	N	48	copy_process    // P0 fork()出P1，进程0是内核进程，不是fork出来，是系统内核初始化创建的第一个进程，跳到main函数就开始执行的，负责给系统做一系列的初始化工作，并且创建进程1(init进程)，而进程1，随后会创建其它用户进程。统一使用P_x-->进程_x
1	J	48	copy_process    // 同一个10ms内，进入就绪队列
0	J	48	schedule        // P0通过sys_pause进入就绪队列，让出CPU
1	R	48	schedule        // P1开始正式运行，通过schedule被调度到
2	N	49	copy_process    // P1 fork()出P2
2	J	49	copy_process    // P2 添加对应ready_list
1	W	49	sys_waitpid     // P1在init里面调用wait，进入wait状态
2	R	49	schedule        // 在P1调用wait之后，通过schedule切换到P2 运行,此时P1是wait状态
3	N	63	copy_process    // P2 通过execve() 建立P3，并加入ready_list里面
3	J	64	copy_process
2	J	64	schedule        // P2 让出CPU，
3	R	64	schedule        // P3 开始运行
3	W	68	sys_pause       // P3 主动调用sys_pause，开始wait？
2	R	68	schedule        // P2 拿到cpu 运行
2	E	74	do_exit         // P2 执行_exit(2);退出
1	J	74	schedule_signal // P1 由于之前waitP2，等待结束，重新就绪
1	R	74	schedule        // P1 开始运行
4	N	74	copy_process    // P1 fork出 P4 shell进程
4	J	74	copy_process    
1	W	74	sys_waitpid     // P1 调用if (pid == wait(&i))进入wait，等待P4
4	R	74	schedule        // P1切到P4, P4 拿到cpu，运行
5	N	106	copy_process    // P4 fork P5
5	J	107	copy_process
4	W	107	sleep_on
5	R	107	schedule
4	J	109	wake_up
5	E	110	do_exit         // P5 退出
4	R	110	schedule        // 切到P4
4	W	115	interruptible_sleep_on // P4 shell进程,等待输入指令
0	R	115	schedule        // P4 切换到P0，P0此时执行 sys_pause进入所谓的idle状态
4	J	467	wake_up         // P4 被唤醒,进入就绪态，因为有shell窗口有输入
4	R	467	schedule        // P4 拿到cpu，运行
6	N	467	copy_process    // P4 shell进程fork出P6
6	J	468	copy_process
4	W	468	sleep_on
6	R	468	schedule
4	J	470	wake_up
6	E	471	do_exit         // P6 处理完成，退出
4	R	471	schedule        // 切回到P4，shell
4	W	471	interruptible_sleep_on // 重复睡眠，等待参数输入，然后唤醒P4，执行
0	R	471	schedule        // 切到P0
```

## 1.2、时间片修改

Linux 0.11中的进程调度时间片主要由两个因素决定：

1. `HZ`宏定义：位于`include/linux/sched.h`中，决定系统时钟中断频率
2. 进程的`counter`和`priority`字段：在`sched.c`的`schedule()`函数中用于调度决策

在当前系统中，`HZ`被定义为100，表示每秒产生100次时钟中断，也就是对应一个时间片（中断的时间间隔）是10ms，。每当发生时钟中断时，当前运行进程的时间片计数器(`counter`)减1，当减到0时会触发进程调度。所以修改时间片就是修改对应的频率即可。

### 10ms时间片

在时间片是10ms一次的通过stat_log.py进行统计结果是

```c
dargon@dd:~/oslab/03_process_file$ ./stat_log.py process.log 
(Unit: tick)
Process   Turnaround   Waiting   CPU Burst   I/O Burst
      0       173355        67           8           0
      1           26         0           2          24
      2           24         4          20           0
      3         3004         0           4        2999
      4       175279        15          92      175172
      5            3         1           2           0
      6            4         0           3           0
      7            4         0           3           0
      8            3         0           3           0
      9            6         1           5           0
     10            3         1           2           0
     11            4         0           3           0
     12            4         0           3           0
     13            4         0           3           0
     14           15         1           7           6
     15            7         0           6           0
     16            3         1           2           0
     17          160         0          13         146
     18           23         0          23           0
     19           42         1          41           0
     20           16         0          15           0
     21           68         1          67           0
     22            3         1           2           0
     23            3         1           2           0
     24            4         0           3           0
     25            6         0           5           0
     26            4         0           3           0
     27            4         0           3           0
     28            4         0           3           0
     29            4         0           3           0
     30            4         1           3           0
     31            3         1           2           0
     32            4         0           3           0
     33            4         0           3           0
     34            4         1           3           0
     35            1         1           0           0
Average:     9780.81      2.75
Throughout: 0.02/s
```

基础系统进程

- **进程0（P0）**：系统空闲进程，负责在没有其他进程需要运行时占用CPU
- **进程4（P4）**：shell进程，等待并处理用户输入的命令Z，更多的资源在shell界面，等待用户输入命令。

CPU资源分配

- 系统空闲进程（P0）仅使用了8 ticks的CPU时间，表明系统整体处于准备好的状态。
- 大量短生命周期的编译子进程（P1、P2、P5-P35）快速获取并释放CPU资源

进程调度效率

- **平均等待时间仅2.75 ticks**，说明Linux 0.11的调度器在处理大量短进程时效率较高。
- 短生命周期进程能够快速执行完成，没有长时间阻塞
- 系统能够有效平衡长周期进程（shell）和短周期进程（编译子进程）的资源分配

基于这些数据，可以观察到Linux 0.11进程调度的几个重要特点：

1. **抢占式调度**：系统能够在进程间快速切换，保证了短进程的响应性能
2. **时间片轮转**：10ms的时间片大小适合处理编译过程中的多种任务类型
3. **优先级隐式体现**：虽然数据中没有直接显示优先级，但从调度行为可以看出，短进程和I/O密集型进程（如shell和编译进程）获得了较好的响应
4. **系统吞吐量**：0.02进程/秒的吞吐量主要受限于I/O操作，而不是CPU处理能力。



### 20ms时间片

```c
dargon@dd:~/oslab/03_process_file$ ./stat_log.py process.log 
(Unit: tick)
Process   Turnaround   Waiting   CPU Burst   I/O Burst
      0         6500        33           0           0
      1           13         3           0          10
      2           10         0          10           0
      3         1506         2           3        1500
      4         6549         9          33        6507
      5            2         0           2           0
      6            2         0           2           0
      7            2         0           2           0
      8            2         0           2           0
      9            4         1           3           0
     10            1         0           1           0
     11            2         1           1           0
     12            2         0           2           0
     13            2         1           1           0
     14            2         0           2           0
     15            2         0           1           0
     16            1         0           1           0
     17            2         0           2           0
     18            1         0           1           0
     19            2         0           2           0
     20           81         1           7          73
     21           11         0          11           0
     22           21         0          21           0
     23            8         0           7           0
     24           35         0          34           0
     25            2         0           1           0
     26            2         0           2           0
     27            2         0           1           0
     28            2         0           2           0
     29            0         0           0           0
Average:      492.37      1.70
Throughout: 0.23/s
```

上下文切换开销减少

- 时间片从10ms增加到20ms，**上下文切换频率理论上减少约50%**
- 更长的时间片执行，减少的上下文切换开销直接提升了系统整体效率

CPU利用率提高

- 更长的时间片使进程能够在CPU上运行更长时间，减少了频繁切换带来的开销
- 对于编译过程中的短进程，虽然时间片变长，但由于它们的实际运行时间远小于时间片，因此并未浪费CPU资源
- 对于I/O密集型进程(如P3、P4)，CPU时间片的增加使得它们在完成I/O后能获得更长的连续执行时间

调度策略效果变化

- Linux 0.11采用的是基于优先级的时间片轮转调度算法
- 时间片增大后，优先级因素对进程调度的影响相对减弱
- I/O密集型进程在完成I/O操作后能够获得更充分的CPU时间

系统响应性平衡

- 虽然时间片增大通常可能影响交互式系统的响应性
- 但在本实验中，由于编译任务主要是批处理性质，更长的时间片反而提高了整体吞吐量
- 系统从更频繁的进程切换转变为更高效的批量处理模式

结论

将Linux 0.11的时间片从10ms(100Hz)修改为20ms(50Hz)后，系统性能得到了显著提升：

1. **资源利用更高效**：减少了上下文切换开销，提高了CPU有效利用率
2. **批处理性能提升**：对于编译这类批处理任务，更长的时间片明显提高了处理效率
3. **整体吞吐量增加**：系统单位时间内能处理更多的进程
4. **I/O操作与CPU执行更协调**：I/O密集型进程在完成I/O后能获得更充分的CPU时间

这些变化表明，时间片的选择应根据系统的主要工作负载类型进行优化。对于以批处理为主的系统，适当增大时间片可以显著提高系统整体性能。

# 2、进程状态的切换

Linux系统里面将一个进程的状态分为5类

```c
#define TASK_RUNNING		0
#define TASK_INTERRUPTIBLE	1
#define TASK_UNINTERRUPTIBLE	2
#define TASK_ZOMBIE		3
#define TASK_STOPPED		4
```

其对应的调用关系如下图

![进程状态及转移关系](https://github.com/Wangzhike/HIT-Linux-0.11/raw/master/3-processTrack/picture/%E8%BF%9B%E7%A8%8B%E7%8A%B6%E6%80%81%E5%8F%8A%E8%BD%AC%E7%A7%BB%E5%85%B3%E7%B3%BB.png)

下面，我们对一个进程从create到running到exit整个生命周期，来跟踪一下进程的调度。

## 2.1、 fork新建进程

fork这个系统调用的时候，会将子进程的状态先设置为`TASK_UNINTERRUPTIBLE`，接着开始为子进程复制并修改父进程的PCB数据。完成后将子进程的状态设置为`TASK_RUNNING`。这个过程对应创建（N）和就绪（J）这两个状态。

```c
// NOTE!: the following statement now work with gcc 4.3.2 now, and you
	// must compile _THIS_ memcpy without no -O of gcc.#ifndef GCC4_3
	*p = *current;	/* NOTE! this doesn't copy the supervisor stack */
	p->state = TASK_UNINTERRUPTIBLE;
	p->pid = last_pid;
	p->father = current->pid;
	/* 省略一系列的复制操作 */
	p->state = TASK_RUNNING;	/* do this last, just in case */
```



## 2.2、 schedule调度

`schedule`函数，首先对所有任务进行检测，由于`p > &FIRST_TASK`所以不包括task0。唤醒任何一个已经得到信号的进程（调用sys_waitpid等待子进程结束的父进程，在子进程结束后，会在此处被唤醒），这里需要记录该进程状态变为就绪态J。

```c
/* check alarm, wake up any interruptible tasks that have got a signal */

	for(p = &LAST_TASK ; p > &FIRST_TASK ; --p)
		if (*p) {
			if ((*p)->alarm && (*p)->alarm < jiffies) {
					(*p)->signal |= (1<<(SIGALRM-1));
					(*p)->alarm = 0;
				}
			if (((*p)->signal & ~(_BLOCKABLE & (*p)->blocked)) &&
			(*p)->state==TASK_INTERRUPTIBLE)
				(*p)->state=TASK_RUNNING;
		}
```

解释一下，下半段的任务状态切换的程序运行逻辑。

* 针对于`_BLOCKABLE`这个宏可以展开`1111 1110 1111 1111 1111 1110 1111 1111`表示意味着 `SIGKILL(9)` 和 `SIGSTOP`(19) 信号不能被阻塞，剩下和可被阻塞的信号集合。

* `(*p)->blocked)`表示当前进程阻塞的信号集合。假设进程 `P1` 阻塞了 `SIGTERM` 信号，那么 `(*p)->blocked` 就是 `1 << (15 - 1)`。
* `(*p)->signal` 是进程 `P1` 接收到的信号集合。假设进程 `P1` 接收到了两个信号， `SIGTERM`（信号编号为 15）和 `SIGALRM`（信号编号为 14）。在二进制表示中，`SIGTERM` 可以表示为 `1 << (15 - 1)`，`SIGALRM` 可以表示为 `1 << (14 - 1)`。所以 `(*p)->signal` 可能是 `(1 << (15 - 1)) | (1 << (14 - 1))`。

执行 **`_BLOCKABLE & (\*p)->blocked`**之后，得到的就是就是 `SIGTERM` 对应的二进制位。其余位被&结果为0了。再执行`~(_BLOCKABLE & (*p)->blocked))`取反操作，得到除了 `SIGTERM` 之外的掩码即是`1111 1111 1111 1111 1011 1111 1111 1111`。再执行`((*p)->signal & ~(_BLOCKABLE & (*p)->blocked))`该 `SIGTERM` 位会被过滤掉，也就是阻塞的被过滤掉，只剩下`SIGALRM` 对应的二进制位。导致后面的结果不为0，由于 `SIGALRM` 未被阻塞，所以结果不为 0。

在操作系统中，这种机制可以让进程在等待某个事件时，能够响应某些未被阻塞的信号。例如，进程 `P1` 在等待磁盘 I/O 操作完成时，如果接收到了 `SIGALRM` 信号，说明设定的定时器时间到了，进程需要立即处理这个信号。通过将进程状态设置为可运行状态，调度器会尽快让进程 `P1` 运行，从而处理这个信号。

阻塞的信号继续被阻塞着，但是需要响应未被阻塞的信号。



接下来就继续看下，就开始选择下一个要运行的任务了，遍历所有的任务，在就绪状态的任务中，选取剩余时间片最大的任务。

选出接下来要运行的任务，其在`task`数组中的下标为`next`，接着，调用`switch_to(next);`切换到该任务中去，



## 2.3、 sys_pause主动睡觉

如上面所述，schedule调度在当系统无事可做的时候，就会调度的进程0去执行，进程0再接着去调用`pause`进行主动睡觉。最终在`sys_pause`里面，又去主动调用`schedule`函数，进行调度。其实就是这样一个循环模式执行task0，等待调度其它有可执行的任务。

`task0`里面持续在`pause`里面执行

```c
/*
 *   NOTE!!   For any other task 'pause()' would mean we have to get a
 * signal to awaken, but task0 is the sole exception (see 'schedule()')
 * as task 0 gets activated at every idle moment (when no other tasks
 * can run). For task0 'pause()' just means we go check if some other
 * task can run, and if not we return here.
 */
	for(;;) pause();
```

实际`pause`的函数执行

```c
int sys_pause(void)
{
	current->state = TASK_INTERRUPTIBLE;
	schedule();
	return 0;
}
```

`schedule()`在进行一轮调度，没有可运行状态的进程时候，依旧选择`task0`接着上面进行循环。



## 2.4、 不可中断睡眠sleep_on

`sleep_on`，利用几个进程因等待同一资源而让出CPU，且将当前进程挂在，调用`sleep_on`函数的各自内核堆栈上的`tmp`指针，并将这些进程通过内核堆栈隐式地链接起来形成一个等待队列。

通过一个例子来说明这一队列的链接过程，进程5,6,7为等待缓冲区而依次调用`sleep_on`的例子。

1. 进程5调用`sleep_on(&buffer_wait)`

```c
tmp = *p(NULL);
*p(buffer_wait) = current(task[5]);

```

接着调用`schedule()`函数让出CPU切换到进程6执行，进程5运行停留在sleep_on函数中。

2. 进程6调用`sleep_on(&buffer_wait)`

```c
tmp = *p(task[5]);
*p(buffer_wait) = current(task[6]);
```

接着调用`schedule()`函数让出CPU切换到进程7执行，进程6运行停留在sleep_on函数中。

3. 进程7调用`sleep_on(&buffer_wait)`

```c
tmp = *p(task[6]);
*p(buffer_wait) = current(task[7]);
```

接着调用`schedule()`函数让出CPU切换到其它进程执行，进程7运行停留在sleep_on函数中。

后面就是等待着进程7被唤醒。



## 2.5、 可中断睡眠

其除了可以用`wake_up`唤醒外，也可以用信号来唤醒。比如`schedule`中一开始就将得到信号的进程先唤醒起来。这里也需要对待唤醒的进程形成同样的队列进行调整。

但是，这里就有一个问题，由于不像`sleep_on`这样只能单一通过`wake_up`进行唤醒操作，这里还能通过信号来进行唤醒，可能唤醒的进程并不是等待队列的头部进程，这里的处理是，如果不是队列头部的进程，则先去唤醒队列头部进程，之后通过`goto repeat`让中间这个进程在去切换到睡眠状态。

这样队列头部进程唤醒之后，就可以接着通过队列的形式，和上面`sleep_on`同样，依次唤醒所有的进程。



## 2.6、 wake_up

唤醒队列头之后，后面会依次唤醒该队列上的所有任务。

后面则不再需要该任务队列的头部指针`*p`了，将其置为NULL，为后续再次将其作为`sleep_on`和`interruptible_sleep_on`的函数做初始化准备。



## 2.7、 do_exit进程退出

`do_exit`将进程的状态设置为`TASK_ZOMBIE` 。子进程终止时，它与父进程的关联还会保持，一直到父进程也正常终止或父进程调用`wait`才因此结束。



## 2.8、 父进程等待子进程退出 sys_waitpid

`wait`系统调用将暂停父进程直到它的子进程结束为止。








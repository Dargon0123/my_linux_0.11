[toc]



# 0. 问题

看完这部分，你应该可以熟悉和回答下面这些问题？

1. `CPU`中断是怎么一回事？
2. 写时复制是如何与页表牵扯上的？
3. `fork`进程返回两次的误解？  

# 1. `main`函数

## 1.0. 如何跳到`main`函数？

综述大概的执行过程。
 `main.c ` 中的代码，是在前面执行完 `boot/head.s`  执行完后，提前压入栈中的代码。在函数 `after_page_tables` 里面进行压栈操作，其中最后一个就是将`main`进行压入，等到`setup_paging`函数调用返回之后，就会从栈里面取出`main`函数地址，进而开始执行。同时，下面的四次压栈操作，就是`main`函数的参数。

```assembly
after_page_tables:
    pushl $0        # These are the parameters to main :-)
    pushl $0
    pushl $0
    pushl $L6       # return address for main, if it decides to.
    pushl $main
    jmp setup_paging
```


## 1.1. `main`的整体框架

* 首先，对物理内存进行功能性的区分，即初步的内存规划，分别通过`mem_init（）`  和 `buffer_init() ` 函数将主内存区域 `main_memory `和缓冲区`buffer`进行一个初始化操作；
* 然后，进行硬件方面的初始化，包括`trap`初始化.块设备.字符设备.屏幕的打印使能.系统时间等等的初始化；
* 接着，任务调用层面的初始化，由于目前还在系统内核中，需要进行手动设置`task0`的上下文环境，以及在`GDT`大表中加载任务段描述符`TSS0`和局部描述符表`LDT0`到相应的位置；
* 再之后，通过模拟中断返回机制，以欺骗`CPU`的形式，从内核态切换到用户态的`task0`中，在`task0`中，通过`fork`系统调用函数，创建子进程`task1`也就是相应的 `init_task` ，由`task1`接着进行下面的 `init `初始化工作；
* 最后，此时的`task0`不会退出，它会在系统切换到空闲状态即`idle`状态下执行，其运行也是通过调用 `pause()` 来主动休眠，使得系统切换到其它需要调度的`task`。

## 1.2. 物理内存的划分与管理

划分
定义系统内存，4块区域。

✨ 随后添加图片

通过 `mem_map[]` 数组管理
使用一个大的数组管理，类似`map`性质，使用过的对数组进行赋值 `map[i] = used` ，主要是管理主内存区域，`main_memory_start/end`

## 1.3. `task0` 内存布局

任务0也是在下面的`task[]`数组里面所对应的 `init_task` 的内存布局，后面称之为`task0`。整个系统是通过这个 `task[64]` 的结构体指针数组来描述对应的每一个运行任务的所有信息。通过这个`task_struct`的结构体来描述该任务的所有上下文，其中包括`pid`.`status`.`fs`信息和`ldt`以及`tss`信息。

```c
struct task_struct * task[NR_TASKS] = {&(init_task.task), };
```


其中包括进程的pid、进程的状态.打开的文件描述符等等。


其中`ldt`和`tss`是非常重要的两个成员。

```c
/* ldt for this task 0 - zero 1 - cs 2 - ds&ss */
    struct desc_struct ldt[3];
/* tss for this task */
    struct tss_struct tss;
```

* `TSS`  表示任务状态段，里面存储着就是寄存器信息，为了保护进程的上下文操作。有了这些寄存器信息，进程切换的时候，可以做到保护和回复进程的上下文信息。其中，
  * 用于找到当前代码的位置`cs:eip`
  * 用于访问数据段的`ds、es、fs、gs、esi和edi` 等
  * 用于访问当前进程堆栈`ss:esp`和内核堆栈寄存器`ss0:esp0` 
  * 用于访问pg_dir地址的寄存器`cr3`
  * 用于访问全局`GDT`表中局部描述符表`LDT`位置的寄存器`ldt` 
  * 通用寄存器 `eax,ebx,ecx,edx,eflags` 
* `LDT`  表示局部描述符表，与`GDT`全局描述符表对应的。内核态里面的代码使用`GDT`里面的数据段和代码段；对于单个任务进程本身，则使用局部的自己的`LDT`里面的数据段和代码段。

通过宏定义直接进行初始化`init_task`的状态

```c
#define INIT_TASK \
/* state etc */	{ 0,15,15, \
/* signals */	0,{{},},0, \
/* ec,brk... */	0,0,0,0,0,0, \
/* pid etc.. */	0,-1,0,0,0, \
/* uid etc */	0,0,0,0,0,0, \
/* alarm */	0,0,0,0,0,0, \
/* math */	0, \
/* fs info */	-1,0022,NULL,NULL,NULL,0, \
/* filp */	{NULL,}, \
	{ \
		{0,0}, \
/* ldt */	{0x9f,0xc0fa00}, \
		{0x9f,0xc0f200}, \
	}, \
/*tss*/	{0,PAGE_SIZE+(long)&init_task,0x10,0,0,0,0,(long)&pg_dir,\
	 0,0,0,0,0,0,0,0, \
	 0,0,0x17,0x17,0x17,0x17,0x17,0x17, \
	 _LDT(0),0x80000000, \
		{} \
	}, \
}
```

通过上面的代码，整理出下面给出对应的上述`init_task`的关键寄存器信息。

<p align="center">
  <img src="F:\Codefield\Code_C\EverNote_typora\Linux0.11总结\L3_Graph\Lab3_poroc-init_task.png" alt="可爱的猫咪" />
  <br>
  <strong>图1-1</strong>
</p>



### 1.3.1. `sys` 内核堆栈和`task0` 的内核堆栈

下图对应的是`cs`这寄存器的段选择子描述符结构：

<p align="center">
  <img src="F:\Codefield\Code_C\EverNote_typora\Linux0.11总结\L3_Graph\segment_selector.png" alt="可爱的猫咪" />
  <br>
  <strong>图1-2</strong>
</p>

* `task0` 的内核堆栈区域：
  从`task[0]`  这个`task_struct` 元素所包含的的`tss` 的`ss0:esp0` 信息，`ss0=0x10,esp0=PAGE_SIZE+(long)&init_task`，对照着上面的寄存器，为`GDT`表的内核数据段的选择。任务0的内核态堆栈指针`esp`初始化为 `PAGE_SIZE+(long)&init_task` ，也就是该task0结构体首地址的4KB偏移处。

* sys的内核堆栈区域：
  在 `boot/head.s`  里面有进行初始化设置，系统的内核堆栈区域。

  ```c
  long user_stack [ PAGE_SIZE>>2 ] ;
  
  struct {
  	long * a;
  	short b;
  	} stack_start = { & user_stack [PAGE_SIZE>>2] , 0x10 }; // ss=0x10,esp=& user_stack [PAGE_SIZE>>2]
  ```

  内核使用的堆栈的栈顶指针在`user_stack`的数组地址的`4Kb`偏移处。

### 1.3.2. `task0` 的线性地址

通过 `sched_init(); `初始化，进行加载`task0`的`0tss`和`0ldt`，`0ldt`里面含有task0的`{null，code，data}`三个段。将里面的代码段和数据段，分别对应到下面段描述符的`64bit`寄存器结构上。

<p align="center">
  <img src="F:\Codefield\Code_C\EverNote_typora\Linux0.11总结\L3_Graph\segment_desc.png" alt="可爱的猫咪" />
  <br>
  <strong>图1-3</strong>
</p>

我们将图1-1的数据，放到上面的寄存器上，来看

代码段`LDT[1] = {0x9f,0xc0fa00}` 

```shell
   63          54 53 52 51 50       48 47 46  44  43    40 39             32
   +-------------+--+--+--+--+--------+--+----+--+--------+----------------+
   | BaseAddress |G |B |0 |A |Seg Lim |P |DPL |S |  TYPE  | BaseAddress    | 
   |   31...24   |  |  |  |V |19...16 |  |    |  | 1|C|R|A|   23...16      |
   |     0x00    |1 |1 |  |L |  0000  |1 |11  |1 | 1|0|1|0|     0x00       |
   +-------------+--+--+--+--+--------+--+----+--+--------+----------------+
   31                               16 15                                  0
   +----------------------------------+------------------------------------+
   |            BaseAddress           |             Segment Limit          |                 
   |             15...0               |                15...0              |
   |             0x0000               |                0x009f              |
   +----------------------------------+------------------------------------+
```

其中，`task0`代码段的线性地址也就是对应的`BaseAddress = 0x0000 0000`，可以看出段限制长度为`0x009f = 640KB`，对应计算，`(0x9f+1) *4 = 640KB`。

数据段`LDT[2] = {0x9f,0xc0f200}` 

```shell
   63          54 53 52 51 50       48 47 46  44  43    40 39             32
   +-------------+--+--+--+--+--------+--+----+--+--------+----------------+
   | BaseAddress |G |B |0 |A |Seg Lim |P |DPL |S |  TYPE  | BaseAddress    | 
   |   31...24   |  |  |  |V |19...16 |  |    |  | 0|E|W|A|   23...16      |
   |     0x00    |1 |1 |  |L |  0000  |1 |11  |1 | 0|0|1|0|     0x00       |
   +-------------+--+--+--+--+--------+--+----+--+--------+----------------+
   31                               17 16                                  0
   +----------------------------------+------------------------------------+
   |            BaseAddress           |             Segment Limit          |                 
   |             15...0               |                15...0              |
   |             0x0000               |                0x009f              |
   +----------------------------------+------------------------------------+
```

其中，两者之间的不同是通过，`type`的值，进行区分`data`和`code`段的。并且，数据段和代码段的基地址都是从`0x0000 0000`开始，长度都是`640KB`，两者是完成重叠的。

对应的640KB所对应的范围：`0x0000 0000~0x000A 0000`



### 1.3.3 . 加载`task0` 后，全局`GDT` 表的更新

每个任务都在`GDT`表中，占两个描述符。系统通过`sched_init`将`task0`的`TSS`和`LDT`加载到`GDT`这张大表中，通过下面的两句话完成加载

```c
set_tss_desc(gdt+FIRST_TSS_ENTRY,&(init_task.task.tss));
set_ldt_desc(gdt+FIRST_LDT_ENTRY,&(init_task.task.ldt));
```

* TSS：任务状态描述符
  里面存储的是，该任务的上下文的所有寄存器值。
* LDT：任务局部描述符表
  里面存储着属于该task的代码段和数据段的信息，包括基地址.段限长、type属性等信息，具体信息对照上图中的 `Segment Descriptor` 寄存器信息。

通过gdb调试，查看加载后的GDT的信息如下

task0的tss和ldt的地址分别打印

```shell
(gdb) p /x &(init_task.task.ldt)
$3 = 0x234f0
(gdb) p /x &(init_task.task.tss)
$4 = 0x23508
```

加载之后的地址：

```shell
(gdb) p /x gdt
$2 = {	{a = 0x0, b = 0x0},  		# gdt[0] = null
		{a = 0xfff, b = 0xc09a00}, 	# gdt[1] = sys_code
         {a = 0xfff, b = 0xc09300},  # gdt[2] = sys_data
         {a = 0x0,b = 0x0}, 		# gdt[3] = null
         {a = 0x35080068, b = 0x8902}, # gdt[4] = task0_TSS
         {a = 0x34f00068, b = 0x8202}, # gdt[5] = task0_LDT
         {a = 0x0,b = 0x0} 			# gdt[n] = null
         <repeats 250 times>}
(gdb) 
```

GDT表里面的内容都是对应着各个任务段的地址，下面将两个地址，通过图的形式进行对应起来。

给出对应的GDT表的内容如下。   

<p align="center">
  <img src="F:\Codefield\Code_C\EverNote_typora\Linux0.11总结\L3_Graph\Lab3_poroc-gdt.png" alt="可爱的猫咪" />
  <br>
  <strong>图1-4</strong>
</p>
1026更新

🤔自己的一个小疑惑点，为什么0x0~0x8这个地址，可以存放下一个64bit（8字节）的数？细细思考后，这确实就是放下的，一个字节表示8bits，比如从0x0~0x8有8个字节，所以可以将`unsigned long a,b;`这个两个32bits的a和b存储在0x0-0x8这个地址处的。其实也就是上面这个GDT中的内存块展开的内存数据块堆起来的。

```shell
地址范围    内容                说明
0x0-0x7    {a=0x0, b=0x0}     gdt[0] - 空描述符
0x8-0xF    {a=0xfff, b=0xc09a00} gdt[1] - 系统代码段
0x10-0x17  {a=0xfff, b=0xc09300} gdt[2] - 系统数据段
0x18-0x1F  {a=0x0, b=0x0}     gdt[3] - 空描述符
0x20-0x27  {a=0x35080068, b=0x8902} gdt[4] - 任务0的TSS
0x28-0x2F  {a=0x34f00068, b=0x8202} gdt[5] - 任务0的LDT
```




## 1.4. 切换到用户态的`task0` 去执行

### 1.4.1. 正常的任务切换

系统在运行多个任务时，通过调用 `switch_to` 函数调用进行任务切换的，使用`ljmp`指令，跳转到新任务的TSS描述符来实现的。比如，任务由t0切换t1时，CPU会自动保存原来的t0的tss上下文到t0的tss中，再将t1任务对应的tss加载当期任务的上下文中。

### 1.4.2. 通过制造“中断“，从内核态切换到用户态

当前环境下，`mian`函数在初始化上面的工作之后，此时还是在内核态运行的。`CPU`的保护机制允许低特权级别的代码通过`trap`操作，进如高级别（内核态）去运行，但是反之则不行。

在之前第2部分系统调用小节，可以通过`int 0x80` 异常（中断），可以从用户态切换到内核态执行相应的系统调用函数，在系统调用执行完后，再通过中断返回的命令，切换到用户态中继续执行。

参考这个，我们可以在内核态中模拟中断返回的场景，实现内核态切换到用户态的过程。通过对`move_to-user_mode` 制造一个中断现场，诱导CPU从内核态切换到用户态。

具体操作：

正常从`int 0x80` 进来的中断，其堆栈的切换是`CPU`自动完成的，在执行完系统调用的`ireq`指令，就是将之前保存在`stack`顶部里面的`eip、cs`顺序弹出，装载到`cpu`的寄存器里面，这就保证了`CPU`会接着`int 0x80`的下一条指令（从`cs:eip`代码段地方来取指令）继续执行。同时，将`stack`中保存的`esp,ss,eflags`寄存器`pop`出来，加载到`cpu`对应的寄存器。

所以，我们这次模拟中断，其实也就是帮`cpu`进行这5个寄存器的`push stack·`操作，最后调用`ireq`返回指令。

```assembly
#define move_to_user_mode() \
__asm__ ("movl %%esp,%%eax\n\t" \
	"pushl $0x17\n\t" \ # ss
	"pushl %%eax\n\t" \ # esp
	"pushfl\n\t" \ # Eflags
	"pushl $0x0f\n\t" \ # cs
	"pushl $1f\n\t" \ # eip
	"iret\n" \
	"1:\tmovl $0x17,%%eax\n\t" \
	"movw %%ax,%%ds\n\t" \
	"movw %%ax,%%es\n\t" \
	"movw %%ax,%%fs\n\t" \
	"movw %%ax,%%gs" \
	:::"ax")
```

寄存器`stack`里面的信息，在执行`ireq`之后，堆栈里面的内容，会相继弹出给到对应的寄存器。如下图：

<p align="center">
  <img src="F:\Codefield\Code_C\EverNote_typora\Linux0.11总结\L3_Graph\Lab3_poroc-move_to_user_mode_stack.png" alt="可爱的猫咪" />
  <br>
  <strong>图1-5</strong>
</p>

* 分析`ss`寻址操作

对于`ss = 0x17`，通过图`1-2`，段选择子描述符可以描述如下：

```shell
   15                                                        3    2        0
   +----------------------------------+------------------------------------+
   |                              index                      |  TI|  RPL   |                 
   |                                 10                      |  1 |   11   |
   |                                                         |    |        |
   +----------------------------------+------------------------------------+
```

其中`Ti =1` ，则表示从`LDT`里面进行寻址操作，`index=2（10）`对应`LDT[2]`（这里对应着整个GDT表来说的）数据段的操作。

* 分析`cs`段寻址操作

同样地,cs=0x0f，其对应寄存器描述符如下：

```shell
   15                                                        3    2        0
   +----------------------------------+------------------------------------+
   |                              index                      |  TI|  RPL   |                 
   |                                 01                      |  1 |   11   |
   |                                                         |    |        |
   +----------------------------------+------------------------------------+
```

其中`Ti =1 `，则表示从`LDT`里面进行寻址操作；`index=1（01）`对应`LDT[1]`代码段的操作。

系统执行完`req` 返回之后，恰巧，使用之前入栈的`ss:esp`和`cs:eip`去执行相应的指令，也就是下面即将开始`task0`的执行。

从上面的`task0`的线性地址范围是` 0x0000 0000 ~0x000A 0000`，占据线性地址空间前面的`640KB`的空间，这个地址，是和内核代码段和数据段的起始地址是 同样的，但是内核的范围是`16MB`。从`[1.3、task0 内存布局]`可以得知，`task0`的页目录表`cr3`的地址是 `&pg_dir`，和内核的页目录表的基地址是一致的。

也就是说，`task0`和内核的代码段和数据段的起始地址是同样的`0x0000 0000` ，页目录表是相同的，所以两者的物理地址也是相同的，只不过是内核段可以访问`16MB`的空间范围，`task0`只能访问`640KB`的空间。

（其实后面`fork`的时候，`task1`复制页表的时候，也只是`640KB`的页表，到`task2`的时候，就是`16MB`的页表了，这也是后话了）

#  2. `task0`的执行

在代码中可以看到

```c
if (!fork()) {		/* we count on this going ok */
		init();
	}
/*
 *   NOTE!!   For any other task 'pause()' would mean we have to get a
 * signal to awaken, but task0 is the sole exception (see 'schedule()')
 * as task 0 gets activated at every idle moment (when no other tasks
 * can run). For task0 'pause()' just means we go check if some other
 * task can run, and if not we return here.
 */
	for(;;) pause();
```

`task0`开始执行后，直接调用`fork`操作了，`fork`出来的就是`task1`了，接着在`task1`里面去执行`init()`任务。当`task0`再次得到调度时，仅仅是主动执行`pause();`函数，来让出CPU使用权，再次调度其它待运行的任务。可以细看上面代码注释内容，这是`linus`当时留下的注释内容。



## 2.1. `fork`的实现机制

通过前面的分析，得知，`fork()`的执行，是`task0`发起的，同样将该函数进行展开，也是我们前面所熟悉的`sys-call`，其形式展开如下。

其中，在`main`函数中，有一些细节，在上面将`fork(),pause()`等系统调用，设置成`inline`性质的内联函数，这部分细节后面通过`fork`函数进行展开。

✨至于为什么是`static inline`的形式，参考`**3.3小节**`

```c
static inline _syscall0(int,fork)
static inline _syscall0(int,pause)
static inline _syscall1(int,setup,void *,BIOS)
static inline _syscall0(int,sync)
```

对应宏定义形式

```assembly
#define _syscall0(type,name) \
type name(void) \
{ \
long __res; \
__asm__ volatile ("int $0x80" \
	: "=a" (__res) \
	: "0" (__NR_##name)); \
if (__res >= 0) \
	return (type) __res; \
errno = -__res; \
return -1; \
}
```

也就是通过`int 0x80`进行的中断，下面就先来看看内核堆栈的情况。

### 2.1.1. `task0`执行`fork()`时内核栈情况

总共的三次寄存器压入栈中：

* 第一次：CPU中断压入

首先通过中断的形式，从`task0`用户态切换到内核态，这个操作，CPU会自动将用户程序在执行时的5个寄存器压入栈中，依次压入顺序分别是`ss,esp,eflags,cs,eip`。就和上面提到的切换到用户态执行task0时，所模拟的中断所压入的寄存器一样。此时，`cs:eip`所指向的代码段是`int 0x80`挨着的下一条指令的位置。该条执行就是

```assembly
#define _syscall0(type,name) \
  type name(void) \
{ \
long __res; \
__asm__ volatile ("int $0x80" \
	: "=a" (__res) \
	: "0" (__NR_##name)); \
if (__res >= 0) \ ## 返回后执行的指令
	return (type) __res; \
errno = -__res; \
return -1; \
}
```

这条语句的作用就是，将`fork`系统调用之后，存储在`eax`中的返回值，提取到`fork()`函数的真正的返回值变量`__res`中，作为`fork()`函数真正的返回值。

* 第二次：中断处理函数：sys_call压入

进入0x80号中断之后，就去调用在`main`函数中`sched_init(void)`初始化的`set_system_gate(0x80,&system_call);`，对应的中断处理函数，`system_call` 函数。

```assembly
system_call:
	cmpl $nr_system_calls-1,%eax
	ja bad_sys_call
	push %ds
	push %es
	push %fs
	pushl %edx
	pushl %ecx		# push %ebx,%ecx,%edx as parameters
	pushl %ebx	
	……
	call *sys_call_table(,%eax,4)
	pushl %eax
```

该函数里面，会将上面6个寄存器再次分别压入栈中。调用sys_fork返回之后，紧接着会去执行 `pushl %eax`。

* 打印当前栈里面的信息

进入该函数之前，我们看看当前栈里面的情况，通过gdb调试断点打在call之前，去看看stack里面的信息。

```shell
(gdb) where
#0  0x00007982 in system_call ()
#1  0x00023000 in ?? ()

(gdb) info frame
Stack level 0, frame at 0x241f8:
 eip = 0x7982 in system_call; saved eip = 0x23000
 called by frame at 0x29f30
 Arglist at 0x241f0, args:
 Locals at 0x241f0, Previous frame's sp is 0x241f8
 Saved registers:
  eip at 0x241f4
  
(gdb) p /x $esp # 当前esp寄存器里所在的地址
$5 = 0x241f4

(gdb) x /16xw $esp # 栈是向低地址方向发展的，栈高地址存储stack里面的内容
0x241f4 <init_task+4052>:       0x00023000      0x000055e8      0x00000021      0x00000017
0x24204 <init_task+4068>:       0x00000017      0x00000017      0x000068e1      0x0000000f
0x24214 <init_task+4084>:       0x00000202      0x00029f10      0x00000017      0x00029f40
0x24224 <stack_start+4>:        0x00000010      0x00000000      0x00000000      0x00000000
```

看下当前寄存器的值

```shell
(gdb) info registers
eax            0x2                 2
ecx            0x55e8              21992
edx            0x21                33
ebx            0x23000             143360
esp            0x241f4             0x241f4 <init_task+4052>
ebp            0x29f28             0x29f28 <user_stack+4072>
esi            0x0                 0
edi            0xffc               4092
eip            0x7982              0x7982 <system_call+12>
eflags         0x293               [ IOPL=0 IF SF AF CF ]
cs             0x8                 8
ss             0x10                16
ds             0x17                23
es             0x17                23
fs             0x17                23
gs             0x17                23
--Type <RET> for more, q to quit, c to continue without paging--
```

🎉·小彩蛋

在往下继续执行几步，发现栈里面多了一项内容，0x00007999。思考这是哪里来的，没有什么再压到栈里面了。

```c
	call *sys_call_table(,%eax,4)
	pushl %eax
```

看完发现是`pushl %eax`语句所在的位置，也即是函数call之前，需要将下次函数调用返回后所执行的语句的地址压入栈中，也就是`call *sys_call_table(,%eax,4)`下一条的`eip = &(pushl %eax)`的地址,（调用返回之后的接着执行的地址）。

```shell
(gdb) x /16xw $esp
0x241f0 <init_task+4048>:       0x00007999      0x00023000      0x000055e8      0x00000021
0x24200 <init_task+4064>:       0x00000017      0x00000017      0x00000017      0x000068e1
0x24210 <init_task+4080>:       0x0000000f      0x00000202      0x00029f10      0x00000017
0x24220 <stack_start>:  0x00029f40      0x00000010      0x00000000      0x00000000
```

更新之后的栈里面的信息如下图。

<p align="center">
  <img src="F:\Codefield\Code_C\EverNote_typora\Linux0.11总结\L3_Graph\Lab3_poroc-L3_05_fork_stack.png" alt="可爱的猫咪" />
  <br>
  <strong>图1-6</strong>
</p>

* `sys_fork()`函数入口

接着根据`__NR_fork`，在这张table`call *sys_call_table(,%eax,4)` 里面，找到对应的`sys_fork`函数。该表如下；

```c
fn_ptr sys_call_table[] = { sys_setup, sys_exit, sys_fork, sys_read,
sys_write, sys_open, sys_close, sys_waitpid, sys_creat, sys_link,
sys_unlink, sys_execve, sys_chdir, sys_time, sys_mknod, sys_chmod,
sys_chown, sys_break, sys_stat, sys_lseek, sys_getpid, sys_mount,
sys_umount, sys_setuid, sys_getuid, sys_stime, sys_ptrace, sys_alarm,
sys_fstat, sys_pause, sys_utime, sys_stty, sys_gtty, sys_access,
sys_nice, sys_ftime, sys_sync, sys_kill, sys_rename, sys_mkdir,
sys_rmdir, sys_dup, sys_pipe, sys_times, sys_prof, sys_brk, sys_setgid,
sys_getgid, sys_signal, sys_geteuid, sys_getegid, sys_acct, sys_phys,
sys_lock, sys_ioctl, sys_fcntl, sys_mpx, sys_setpgid, sys_ulimit,
sys_uname, sys_umask, sys_chroot, sys_ustat, sys_dup2, sys_getppid,
sys_getpgrp, sys_setsid, sys_sigaction, sys_sgetmask, sys_ssetmask,
sys_setreuid,sys_setregid, sys_iam, sys_whoami, sys_iam2, sys_whoami2 };
```

并跳转到`sys_fork`函数去执行。

接着，继续往下看就是sys_fork的真正执行函数了。一步一步分析里面的函数，也是fork的精髓所在了。

```c
sys_fork:
	call find_empty_process
	testl %eax,%eax
	js 1f
	push %gs
	pushl %esi
	pushl %edi
	pushl %ebp
	pushl %eax
	call copy_process
	addl $20,%esp
1:	ret
```

逐个看下里面所调用的函数。

### 2.1.3. 调试`find_emoty_process`

``` c
int find_empty_process(void)
{
	int i;

	repeat:
		if ((++last_pid)<0) last_pid=1; // 防止long整数溢出 
		for(i=0 ; i<NR_TASKS ; i++) // 遍历找一个没有被使用的last_pid 全局变量
			if (task[i] && task[i]->pid == last_pid) goto repeat;
	for(i=1 ; i<NR_TASKS ; i++) // 再遍历找一个没有被使用的task[i]
		if (!task[i])
			return i;
	return -EAGAIN;
}

```

该函数主要是2个for循环

第一个：为新创建的`task1`，分配`pid`，通过`last_pid`这个全局变量在递增的方向上，找到一个当前未使用的`last_pid`的值，为`task1->pid`找到唯一值。pid可以达到最大

第二个：找名字之后，再接着在`task`数组里面，找一个`task[i]`的空闲项。并且返回`i`值。

`task`数组就是存放当前系统的所有任务上下文即是`PCB`的，最大存储个数为`NR_TASKS`。这里可以明显看出，进程`pid`值和对应该任务的`pcb`存储在`task`数组下标值并不是一一对应的，除了当前的`task0`外。

* 第三次压栈：`sys_fork`操作

该函数返回之后，sys_fork函数，开始新一波的压栈操作，将 `gs,esi,edi,ebp,eax`其中`eax`就是对应的`find_empty_process()`函数的返回值。接着去调用`copy_process`函数来为新`task`创建所运行的上下文环境。

再次通过`gdb`查看下当前stack里面的内容。

当前寄存器内容

```shell
eax            0x1                 1
ecx            0x1                 1
edx            0x0                 0
ebx            0x23000             143360
esp            0x241e0             0x241e0 <init_task+4032>
ebp            0x29f28             0x29f28 <user_stack+4072>
esi            0x0                 0
edi            0xffc               4092
eip            0x7aa0              0x7aa0 <sys_fork+14>
eflags         0x202               [ IOPL=0 IF ]
cs             0x8                 8
ss             0x10                16
ds             0x10                16
es             0x10                16
fs             0x17                23
gs             0x17                23
--Type <RET> for more, q to quit, c to continue without paging--
```

其`stack`里面的内容更新

```shell
(gdb) x /16xw $esp
0x241dc <init_task+4028>:       0x00000001      0x00029f28      0x00000ffc      0x00000000
0x241ec <init_task+4044>:       0x00000017      0x00007999      0x00023000      0x000055e8
0x241fc <init_task+4060>:       0x00000021      0x00000017      0x00000017      0x00000017
0x2420c <init_task+4076>:       0x000068e1      0x0000000f      0x00000202      0x00029f10
```



进入`copy_process`前，当前的内核堆栈图更新如下（注意进入之后，你去看栈里面的信息，也会多一个函数调用之前的eip的寄存器的值，这点在上面的🎉小彩蛋里面有所陈述）：

<p align="center">
  <img src="F:\Codefield\Code_C\EverNote_typora\Linux0.11总结\L3_Graph\Lab3_poroc-l3_06_fork_stack_3.png" alt="可爱的猫咪" />
  <br>
  <strong>图1-7</strong>
</p>



有了这些`stack`里面的寄存器的信息，我们接着看下下面这个函数。

### 2.1.4. 调试`copy_process`

顾名思义，进程的复制操作。先看下函数的参数的传递。

```c
/*
 *  Ok, this is the main fork-routine. It copies the system process
 * information (task[nr]) and sets up the necessary registers. It
 * also copies the data segment in it's entirety.
 */
int copy_process(int nr,long ebp,long edi,long esi,long gs,long none,
		long ebx,long ecx,long edx,
		long fs,long es,long ds,
		long eip,long cs,long eflags,long esp,long ss)
```

栈里面参数的传递顺序是逆着来的，比如上面的`eax`就会复制给参数表里面的`nr`，

我们现在可以将参数通过上面的栈里面的信息进行一一对应下来，一个都没问题。

```shell
(gdb) stepi
0x00007aa1 in sys_fork ()
copy_process (nr=1, ebp=171816, edi=4092, esi=0, gs=23, none=31129, ebx=143360, ecx=21992,
    edx=33, fs=23, es=23, ds=23, eip=26849, cs=15, eflags=514, esp=171792, ss=23)
    at fork.c:74
```

函数里面首先通过`p = (struct task_struct *) get_free_page();` 获得一个`4KB`的`page`大小的内存，然后直接通过`*p = *current;`复制当前`task`的`PCB`，复制完之后，当前子进程的代码段`cs:eip`，数据段`ds,es,fs,gs,esi,edi`，用户态堆栈`ss:esp`寄存器是一样的。

但是有一些是必要的修改：1）子进程的`pid`设置为之前更新的`last_pid` ；2）子进程的状态设置为不可运行的状态`TASK_UNINTERRUPTIBLE`等待初始化完成之后，再设置为可调度的状态`TASK_RUNNING`；3）`p->tss.eax = 0;`子进程的`eax`设置为`0`，`mian`调度后子进程在返回处开始执行的返回值；4）`p->tss.ldt = _LDT(nr);`加载自己的`ldt`局部描述符；5）调用`copy_mem(nr,p)`，设置自己的`LDT`；6）进而，在调度`copy_page_tables`从`task0`直接复制页表内容，并将页表项的属性改为只读性质，同是为“写时复制”埋下基础；7）最后返回`copy_process`中进行`TSS`和`LDT`的设置，并将新进程的`last_pid`作为返回值，返回到`sys_fork`里面。

`task1`的主要寄存器；



### 2.1.5. 调试`copy_mem`

之前，讲过系统的内存管理机制，通过分段和分页操作，系统为每个task分配`nr * 0x4000000 `即是64MB的线性地址空间。并设置对应的LDT[1]和LDT[2]的内容。

```c
new_data_base = new_code_base = nr * 0x4000000;
p->start_code = new_code_base;
set_base(p->ldt[1],new_code_base);
set_base(p->ldt[2],new_data_base);
```

接下来，开始页表的复制

```c
// old = 0; new = 64MB; limit = 640KB
copy_page_tables(old_data_base,new_data_base,data_limit);
```

这是一段复杂的逻辑，目的是将进程0和进程1的线性地址，同时映射到相同的物理地址空间上。

总之，最终的效果就是：

假设现在正在运行进程 0，代码中给出一个虚拟地址 0x03，由于进程 0 的 LDT 中代码段基址是 0，所以线性地址也是 0x03，最终由进程 0 页表映射到物理地址 0x03 处。

假设现在正在运行进程 1，代码中给出一个虚拟地址 0x03，由于进程 1 的 LDT 中代码段基址是 64M，所以线性地址是 64M + 3，最终由进程 1 页表映射到物理地址也同样是 0x03 处。

<p align="center">
  <img src="F:\Codefield\Code_C\EverNote_typora\Linux0.11总结\L3_Graph\PDE_struct.png" alt="可爱的猫咪" />
  <br>
  <strong>图1-8 PDE</strong>
</p>


位描述

<p align="center">
  <img src="F:\Codefield\Code_C\EverNote_typora\Linux0.11总结\L3_Graph\PDE_strcu_detail.png" alt="可爱的猫咪" />
  <br>
  <strong>图1-9 PDE_datail</strong>
</p>


同时，`this_page &= ~2;`这样一句话，将第2个bit，置0操作，对照上面寄存器可知，其改变成了只读属性，也就是为**写时复制**做好了打算。(曾经在面试一家大厂时，遇到过这个问题。🤯)



## 2.2. 返回后的栈信息

* 退出system_call的情况。

```shell
(gdb) x /20xw $esp
0x241f0 <init_task+4048>:       0x00000001      0x00023000      0x000055e8      0x00000021
0x24200 <init_task+4064>:       0x00000017      0x00000017      0x00000017      0x000068e1
0x24210 <init_task+4080>:       0x0000000f      0x00000202      0x00029f10      0x00000017
0x24220 <stack_start>:  0x00029f40      0x00000010      0x00000000      0x00000000
0x24230:        0x00000000      0x00000000      0x00000000      0x00000000
```

栈信息出来，恢复到给自己对应的寄存器信息里面

```shell
(gdb) x /20xw $esp
0x2420c <init_task+4076>:       0x000068e1      0x0000000f      0x00000202      0x00029f10
0x2421c <init_task+4092>:       0x00000017      0x00029f40      0x00000010      0x00000000
```

寄存器信息

```shell
eax            0x1                 1                                                     
ecx            0x55e8              21992                                                 
edx            0x21                33                                                   
ebx            0x23000             143360                                                 
esp            0x2420c             0x2420c <init_task+4076>                             
ebp            0x29f28             0x29f28 <user_stack+4072>                             
esi            0x0                 0                                                     
edi            0xffc               4092                                                  
eip            0x79ef              0x79ef <ret_from_sys_call+69>                         
eflags         0x246               [ IOPL=0 IF ZF PF ]                                   
cs             0x8                 8                                                     
ss             0x10                16                                                     
ds             0x17                23                                                   
es             0x17                23                                                   
fs             0x17                23                                                     
gs             0x17                23     
```

* 退出cpu中断信息

将之前压入的eip弹出来，即是`eip = 0x000068e1`的，此时代码跳转到0x000068e1位置处继续执行。

<p align="center">
  <img src="F:\Codefield\Code_C\EverNote_typora\Linux0.11总结\L3_Graph\Lab3_poroc-L3_05_fork_stack.png" alt="可爱的猫咪" />
  <br>
  <strong>图1-10</strong>
</p>



恰好，如此图刚进来时的原样。



# 3. 一些细节



## 3.1. `gdb`调试页表的复制数量

我们通过复制前后打印内容，来看页表内容的变化形式。

* 复制前（task0）

页表在`task0`的时候，初始化的时候有`4`个页目录项，由于一个页目录含有`1024`个页表，每个页表项可管理`4Kb`的空间，所以每一个页目录可管理`4MB`的空间。`Linus`在初始化的时候备注只需要`16MB`的空间就可以了，需要额外的可以在后面进行扩张。

并且这些表全部在`0x0`位置处，由`cr3`寄存器指向该地址。打印地址

```shell
(gdb) p /x $cr3
$2 = 0x0
(gdb) x /20xw 0x0
0x0 <startup_32>:       0x00001027      0x00002007      0x00003007      0x00004027
0x10 <startup_32+16>:   0x00000000      0x00000000      0x00000000      0x00000000
0x20 <startup_32+32>:   0x00000000      0x00000000      0x00000000      0x00000000
0x30 <startup_32+48>:   0x00000000      0x00000000      0x00000000      0x00000000
0x40 <startup_32+64>:   0x00000000      0x00000000      0x00000000      0x00000000
```

可以看到放置的有4个页目录项，但是，我们在复制页表的时候，由`task0`到`task1`的时候，比较特殊，仅仅复制`160`个页表，也就是说，	`task0`只映射到物理内存的`160 * 4KB = 640Kb`的大小，源码如下

```c
nr = (from==0)?0xA0:1024; // 0xa0 = 160
```

我们确认下，是否是`160`个页表，根据上图1-8和1-9中`PDE/PTE`的结构来看，得到地址

```shell
(gdb) p /t 0x00001027
$4 = 0001 0000 0010 0111 # 则对应的页表地址 0x0000 1000 低12bits 为0
```



* 复制后

页目录项，则多了一个

```shell
(gdb) x /20xw 0x0
0x0 <startup_32>:       0x00001027      0x00002007      0x00003007      0x00004027
0x10 <startup_32+16>:   0x00000000      0x00000000      0x00000000      0x00000000
0x20 <startup_32+32>:   0x00000000      0x00000000      0x00000000      0x00000000
0x30 <startup_32+48>:   0x00000000      0x00000000      0x00000000      0x00000000
0x40 <startup_32+64>:   0x00fde007      0x00000000      0x00000000      0x00000000
```

对应的我们通过根据PDE/PTE的寄存器结构来看，得到地址

```shell
(gdb) p /t 0x00fde007
$5 = 1111 1101 1110 0000 0000 0111 # 则对应的页表地址 0xfde000 低12bits 为0
```

打印下看看是否是160项

```shell
(gdb) x /170xw 0xfde000
0xfde000:       0x00000065      0x00001025      0x00002005      0x00003005
0xfde010:       0x00004005      0x00005065      0x00006065      0x00007025
0xfde020:       0x00008025      0x00009005      0x0000a025      0x0000b025
0xfde030:       0x0000c005      0x0000d005      0x0000e025      0x0000f005
0xfde040:       0x00010005      0x00011005      0x00012005      0x00013005
0xfde050:       0x00014025      0x00015025      0x00016025      0x00017025
0xfde060:       0x00018025      0x00019025      0x0001a005      0x0001b005
0xfde070:       0x0001c025      0x0001d005      0x0001e005      0x0001f005
0xfde080:       0x00020005      0x00021005      0x00022005      0x00023065
0xfde090:       0x00024065      0x00025025      0x00026065      0x00027065
0xfde0a0:       0x00028065      0x00029065      0x0002a065      0x0002b065
0xfde0b0:       0x0002c065      0x0002d065      0x0002e065      0x0002f065
0xfde0c0:       0x00030065      0x00031065      0x00032065      0x00033065
0xfde0d0:       0x00034065      0x00035065      0x00036065      0x00037065
0xfde0e0:       0x00038065      0x00039065      0x0003a065      0x0003b065
0xfde0f0:       0x0003c065      0x0003d065      0x0003e065      0x0003f065
0xfde100:       0x00040065      0x00041065      0x00042065      0x00043065
0xfde110:       0x00044065      0x00045065      0x00046065      0x00047065
0xfde120:       0x00048065      0x00049065      0x0004a005      0x0004b005
0xfde130:       0x0004c005      0x0004d005      0x0004e005      0x0004f005
0xfde140:       0x00050005      0x00051005      0x00052005      0x00053005
0xfde150:       0x00054005      0x00055005      0x00056005      0x00057005
0xfde160:       0x00058005      0x00059005      0x0005a005      0x0005b005
0xfde170:       0x0005c005      0x0005d005      0x0005e005      0x0005f005
0xfde180:       0x00060005      0x00061005      0x00062005      0x00063005
0xfde190:       0x00064005      0x00065005      0x00066005      0x00067005
0xfde1a0:       0x00068005      0x00069005      0x0006a005      0x0006b005
0xfde1b0:       0x0006c005      0x0006d005      0x0006e005      0x0006f005
0xfde1c0:       0x00070005      0x00071005      0x00072005      0x00073005
0xfde1d0:       0x00074005      0x00075005      0x00076005      0x00077005
0xfde1e0:       0x00078005      0x00079005      0x0007a005      0x0007b005
0xfde1f0:       0x0007c005      0x0007d005      0x0007e005      0x0007f005
0xfde200:       0x00080005      0x00081005      0x00082005      0x00083005
0xfde210:       0x00084005      0x00085005      0x00086005      0x00087005
0xfde220:       0x00088005      0x00089005      0x0008a005      0x0008b005
0xfde230:       0x0008c005      0x0008d005      0x0008e005      0x0008f005
0xfde240:       0x00090025      0x00091005      0x00092005      0x00093005
0xfde250:       0x00094005      0x00095005      0x00096005      0x00097005
0xfde260:       0x00098005      0x00099005      0x0009a005      0x0009b005
0xfde270:       0x0009c005      0x0009d005      0x0009e005      0x0009f005 # 后面10项为空的
0xfde280:       0x00000000      0x00000000      0x00000000      0x00000000
0xfde290:       0x00000000      0x00000000      0x00000000      0x00000000
0xfde2a0:       0x00000000      0x00000000
```

确实是复制了160项。

并且每个页表都是`0x xxxx xxx5`5则表示`0101`从页表寄存器上来看，对应的是读写为为0，表示只读状态，为前面提到的写时复制准备下了基础。



## 3.2. 关于`fork()API`“一次调用两次返回”的误解

* 主要分析点

进行多进程编程时，fork函数根据返回值的不同，判断是父进程还是子进程。返回的值，主要是看`eax`寄存器里面的值。下面从子进程和父进程两个角度来看这个过程，一目了然。

* 子进程

在`copy_process` 的时候，会设置子进程的eax寄存器的值为0，等到切换到子进程时，通过子进程自己的`PCB`会将自己的`tss`中的所有寄存器，装载到`cpu`里面，所以子进程在`fork()`返回的那个节点，开始执行，其`eax`值为0。这时候`eax`寄存器的值对应的就是`fork()`的返回值就是`0`。

接着执行`main()`下面`init()`的代码：

```c
if (!fork()) {		/* we count on this going ok */
    init();
}
```

* 父进程

父进程在`copy_process` 函数会将子进程的`pid`号，对应代码`return last_pid;`也就是从函数`find_empty_process()`找到的未使用的全局变量 `last_pid`作为返回值，返回到`sys_fork()`函数。接着，`sys_fork()`函数返回到中断处理函数`system_call`中。这个时候，`system_call`会将`sys_fork()`的返回值即`last_pid`压入栈中。接着执行`sys_call`里面的函数。如下：

```assembly
call *sys_call_table(,%eax,4)
pushl %eax 	# 将存储着返回的last_pid的eax寄存器压入栈中

movl current,%eax
cmpl $0,state(%eax)		# state
jne reschedule
cmpl $0,counter(%eax)		# counter
je reschedule
```

再接着，判断是否需要调度，需要调度的话，执行`reschedule`函数，此后就是调度到其他进程进行运行。待其他进程的时间片运行结束之后，还是要切换到这里来。就是说无论父进程是否被调度，都会一直执行到`system_call`返回用户态的过程，只不过可能会有时间的间隔之外。也就是最终，其返回到用户态时，`eax`寄存器里面的值存储的就是相应的`last_pid`的值。

这是<u>下划线文本</u>。

回顾\> <span style="color: grey;"><u>**2.1.1、`task0`执行`fork()`时内核栈情况**</u></span>，`CPU`从内核态返回到用户态的时候，执行`iret`之后的紧接着的指令，就是执行中断`int $0x80`前的下一个准备执行的指令，就是`cs:eip`寄存器里面的地址，也就是`0x000068e1`这个地址，对应的代码就是下面将返回值`eax`寄存器的值存入到`_res`变量里面。

```assembly
__asm__ volatile ("int $0x80" \
	: "=a" (__res) \
	: "0" (__NR_##name)); \
if (__res >= 0) \ ## 返回后执行的指令
	return (type) __res; \
```

同时，还是在`copy_process` 中，其`fork`出来的子进程的`cs:eip`赋值，也是复制的父进程的，也就是说父进程从中断返回到用户态接着执行的`cs:eip`的代码的地址，所以子进程在开始的时候，就是处于用户态的。两者的代码段寄存器`cs:eip`是完全一样的，都是接着执行上面的，**将eax寄存器里面的返回值，存入到_res变量中，只不过，两者的eax中所放置的值不一样**，这就相当于，父进程从`fork()`函数这里返回，子进程从这里开始执行，所以看上去，就像返回了两次。一个是返回，一个是开始执行。



## 3.3. `main`函数中的`syscall`内联函数的原因

我们分析一下这个原因，反证法看一下，假如没有使用`inline`的形式，会发生什么？

* 背景

`copy_process`在处理进程1（init进程）的`640KB`物理内存对应的页表项时，将其属性设置为只读。对应的父进程，进程0的页表项的可读写的属性是不变的。因此，进程0创建出进程1的之后，进程0对内存中这`640KB`的数据仍是可读可写的，但是创建出的进程`1`却只是可读属性的。

* 现象

假设该`fork`不是以`inline`的形式出现的，而是进程`0`通过调用形式实现的，那么进程`0`调用`fork`函数的过程中，一定会用到用户态的堆栈，所以，在进程0调用完fork之后，其用户栈一定不是空的。

在fork返回后，系统进行一个调度，1）可能是进程0先于进程1 执行，这没什问题；2）但是也可能进程1先于进程0执行。如果是进程1先执行，那么对于进程1的`640KB`的可读属性来说，就有点挑战了。（这部分细节参考**问题3.2**）

一旦进程1开始写数据或者进行函数调用就会引发写时复制，函数调用时，由于局部变量是存储在用户栈中，且需要用户栈来传递参数和保存函数返回地址，这个用户栈也是属于进程1的640KB空间的，自然是只读的，所以进程1在做写数据和函数调用时，都会引发写时复制，从而引发，内存管理程序会为进程1分配新的一页内存作为进程1的用户栈。

而进程1的用户栈最初也都是从进程0完全copy过来的，内存管理程序在分配这页内存给进程1的时候，初始化数据的时候，也会将进程0的用户栈的内容全部copy过来，以保证进程1和进程0的用户栈数据是相同的。

所以，此时，由于进程0的用户栈并不是空的，由于进行`fork`函数的调用，里面一定包含着`fork`函数的返回地址，而这个数据对于进程1来说，是没有意义的，假如进程1接下来的要执行从栈中取数据，那可能`pop`出来的就是`fork`的返回地址（针对与进程0是合理的返回地址），这样就造成进程1的栈出来的数据错误。

* 结论

为了避免进程0使用用户态堆栈导致进程1的数据混乱，需要保证进程0在进程1执行操作之前，禁止使用其用户栈，也得保证进程0调用完`fork`之后，仍然不能使用用户栈，这里主要是因为进程0调用完`fork`之后，进行系统调度可能于一直没有调度到进程1的情况下，进程0会接着执行`pause`了，这样也是会相应的调用用户栈的，所以对应的`fork`和`pause`都需要一内联形式实现。

`pause`设置为`inline`形式是同样的，进程1未调度之前，先调度了进程0，此时会将fork的返回地址从栈里面弹出来，然后pause，同样是函数调用，同样会使用到栈来存储。这是再去切换进程1，写时复制，栈复制之后，又会带入错误的地址。

# 4. 进入shell

## 文件系统梳理

可以通过gdb的方式，把内容打印出来，看看里面的具体数据，会有更多的帮助。



## P2的创建

* 问题1：弄清楚P3是在哪里进行创建的，是谁创建的，main函数里面的具体位置。进程跟踪的时后，返现的，解释不通，需要深入看下这里的机制？
* 问题2：shell程序的执行流程？

P1进程通过下面

```c
if (!(pid=fork())) { // P2开始
		close(0);
		if (open("/etc/rc",O_RDONLY,0)) // 将文件描述0从/dev/tty0指向为/etc/rc
			_exit(1);
		execve("/bin/sh",argv_rc,envp_rc);
		_exit(2);
	}
```

文件描述符0重新更改了指向。P2进程通过execve的执行，通过中断跳转的形式，但是这个中断没有返回，直接将寄存器

```c
	eip[0] = ex.a_entry;		/* eip, magic happens :-) */
	eip[3] = p;			/* stack pointer */
	return 0;
```

通过图1-8，可以看出对应的寄存器，eip和esp都被调换了 ，所以这个esecve系统system_call中断，在返回后，直接就去被更改过的eip和esp接着执行命令。取到的指令也就是`/bin/sh`这个二进制的程序，也就是我们熟悉的shell程序。插入一个细节点，这里其实只是将`/bin/sh`前1KB的数据加载到内存里面了，但是其余的数据并没有加载。

等到system_call中断按照新的eip和esp指针去寻址，它会跳转到的具体地址是哪里的，不知道，但是肯定是在P2所对应的线性地址所在64M范围内的。这是根据`/bin/sh`这个程序编译之后的前1KB数据里面的	`a.a_entry`进行决定的。拿到这个地址去执行程序的时候，会发现，啊，转化到实际物理地址时，没有这个地址，此时会触发对应的缺页中断，P位=0的情况。然后，才会把硬盘里所有的`/bin/sh`相关数据加载到内存里面。

缺页中断返回后，继续从这里这个`a.a_entry`去执行，此时，这里的线性地址已经能通过对应的页表映射到物理地址上了，已经开始有对应的数据了。可以接着执行`/bin/sh`这个程序了。

进入这个shell之前，我通过实验3的进程跟踪，去打印出来的进程之间的关系如下

```c
1	W	49	sys_waitpid     // P1在init里面调用wait，进入wait状态
2	R	49	schedule        // 在P1调用wait之后，通过schedule切换到P2 运行,此时P1是wait状态
3	N	63	copy_process    // P2 通过execve() 建立P3，并加入ready_list里面
3	J	64	copy_process
2	J	64	schedule        // P2 让出CPU，
3	R	64	schedule        // P3 开始运行
```

在P2运行期间，创建P3，这个P3在代码里面其实是没有看到的，在shell这里可以做出解释。

回到上面的话题中，此时，我们其实处于一个以`"/etc/rc"`为输入的shell进程。本身shell的机制就是，fork+execve去执行命令的。当时输入是一个完整的普通文件时，比如`"/etc/rc"`，那文件被读取后，shell会自动退出。当该shell开始读到这个文件，也就是这个`/bin/sh`程序里面，去fork出P3，接着执行的。

然后，P3通过sys_pause进行进入wait的状态。P2就是此时的shell进程退出。

P2退出之后，下面waitP2的P1开始执行了。

```c

if (pid>0) // P1继续
		while (pid != wait(&i))  // 等待P2退出
			/* nothing */;
	while (1) {
		if ((pid=fork())<0) { // fork出P4,以/dev/tty0为标准输入的shell
			printf("Fork failed in init\r\n");
			continue;
		}
		if (!pid) {
			close(0);close(1);close(2);
			setsid();
			(void) open("/dev/tty0",O_RDWR,0);
			(void) dup(0);
			(void) dup(0);
			_exit(execve("/bin/sh",argv,envp));
		}
		while (1)
			if (pid == wait(&i))
				break;
		printf("\n\rchild %d died with code %04x\n\r",pid,i);
		sync();
	}
```

P1在fork出P4之后，就是标准的以/dev/tty0为标准输入的shell，P1就开始进入wati状态了。

P4shell进程就等待着用户在shell里面输入命令，然后，按照shell程序，固有的操作，fork+execve来搞一个新的进程，运行这个指令，运行完之后，结束这个进程。系统会在最初的P0和P4里面循环，等待着用户通过shell输入命令，来执行。
















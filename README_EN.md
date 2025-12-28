# my_linux_0.11

[中文版本](README.md) | English Version

Debug and learning linux-0.11. Talk is cheap, show me your code.

---

## 📖 Introduction

This repository is used for learning and documenting the `Linux-0.11` kernel source code. Through chapter-by-chapter analysis, the process of debugging the system step by step is recorded here and continuously updated. By slowly analyzing the source code and peeking into the details of the system, I was deeply impressed by these technical details. Many of these details can be applied to our actual work, serving as a guiding ideology worth savoring for every technical practitioner.

> For environment setup, please refer to the document `README_OLD.md`

---

## ✨ Features

- 📚 **Systematic Learning** - Organized by chapters, from system boot to kernel mechanisms
- 🐛 **Debug Driven** - Deep understanding of kernel principles through actual debugging
- 🔍 **Source Code Analysis** - Line-by-line interpretation of Linux 0.11 core code
- 📝 **Detailed Comments** - Key code with Chinese comments

---

## 📂 Reading Order

| Chapter | Topic | Type | Link |
|---------|-------|------|------|
| L1 | System Boot Process | 📝 Notes | [View](https://github.com/Dargon0123/Linux-0.11/blob/Lab1_OS_Boot/Lab1_OS_Booting.md) |
| L2 | System Call Chain Analysis | 📝 Notes | [View](https://github.com/Dargon0123/Linux-0.11/blob/Lab2_Sys_Call/README.md) |
| L3 | Details of Process Creation | 📝 Notes | [View](https://github.com/Dargon0123/my_linux_0.11/blob/3_trace_task/03_process_file/Lab3_Track.md) |
| L3 | Process Tracking Experiment | 🔬 Experiment | [Code Branch](https://github.com/Dargon0123/my_linux_0.11/tree/3_trace_task) |
| L4 | Kernel Stack Switching | 🔬 Experiment | [Code Branch](https://github.com/Dargon0123/my_linux_0.11/tree/3_trace_task) |

> 💡 **Note**: L3 contains two dimensions - 📝 theoretical notes and 🔬 experiment code
> 
> 🔭 More chapters coming soon...

---

## 🚀 Quick Start

### Prerequisites

- Linux/macOS/Windows (WSL)
- GCC Compiler
- Bochs Emulator
- Make Tool

### Run the Project

```bash
# Run with Bochs
./run

# Debug with GDB
./rungdb
```

---

## 📁 Directory Structure

```
my_linux_0.11/
├── linux-0.11/          # Linux 0.11 source code
│   ├── boot/            # Boot loader code
│   ├── kernel/          # Kernel core
│   │   ├── blk_drv/     # Block device drivers
│   │   ├── chr_drv/     # Character device drivers
│   │   └── math/        # Math coprocessor
│   ├── mm/              # Memory management
│   ├── fs/              # File system
│   ├── lib/             # Library functions
│   └── include/         # Header files
├── bochs/               # Bochs configuration
├── hdc/                 # Hard disk image
└── scripts/             # Run scripts
```

---

## 📚 References

- [Linux 0.11 Source (yuan-xy)](https://github.com/yuan-xy/Linux-0.11)
- [HIT Linux 0.11](https://github.com/Wangzhike/HIT-Linux-0.11)

---

## 🤝 Contributing

Issues and Pull Requests are welcome!

---

## 📄 License

This project is open sourced under the [GPL-3.0](LICENSE) license.

---

## 📧 Contact

- GitHub: [@Dargon0123](https://github.com/Dargon0123)
- Project Issues: [GitHub Issues](https://github.com/Dargon0123/my_linux_0.11/issues)

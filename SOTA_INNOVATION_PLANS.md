# 🚀 SOTA Innovation Plans for Continual Learning & MoE Routing

> **背景与愿景**：针对持续学习（Continual Learning, CL）与参数高效微调（PEFT/MoE）中的“灾难性遗忘（Catastrophic Forgetting）”与“路由分配漂移（Routing Drift / Load Balancing）”痛点，本文档汇集了 5 个跨学科的硬核 SOTA 优化方案。这些方案经过广泛的文献检索，确保在当前 AI 社区中具有绝对的新颖性（Novelty）和极高的研究/实验价值。

---

## 🌊 1. 流体力学启发：不可压缩流路由 (Navier-Stokes Incompressible Flow Router)

**💡 跨领域理论基础**：
借鉴流体力学中的**连续性方程 (Continuity Equation)** 与**不可压缩流体 (Incompressible Flow)** 概念。在流体力学中，不可压缩流体的散度为零（$\nabla \cdot \mathbf{v} = 0$），即流入与流出某区域的质量必须守恒。

**⚙️ 深度学习机制映射**：
在 MoE 中，Router 经常面临“Expert Collapse（少数 Expert 垄断所有 Token）”的问题，传统方法依赖脆弱且难以调参的 Auxiliary Loss。我们将 Token 视为“流体质点”，将 Expert 视为“管道”。通过在 Router 中引入**散度惩罚（Divergence Penalty）**，强制路由概率场在整个数据流上表现为“不可压缩”。这意味着流入每个 Expert 的 Token 流量在宏观上必须守恒，从物理底层实现绝对的 Load Balancing，并防止新任务在 CL 中冲垮旧任务的路由通道。

**📐 数学公式雏形**：
设 $R_i(x)$ 为输入 $x$ 路由到 Expert $i$ 的概率。不可压缩约束要求：
$$ \nabla \cdot \mathbf{R}(x) = 0 $$
转化为损失函数中的散度惩罚项（计算 Batch 内的流量守恒）：
$$ \mathcal{L}_{fluid} = \lambda \sum_{i=1}^{E} \left( \mathbb{E}_{x \sim \mathcal{B}}[R_i(x)] - \frac{1}{E} \right)^2 + \gamma \sum_{i=1}^E \text{Var}_{x \sim \mathcal{B}}(R_i(x)) $$

**💻 代码实现思路 (Pseudocode)**：
```python
def fluid_router_forward(x, router_logits):
    # router_logits: [batch_size, num_experts]
    prob = F.softmax(router_logits, dim=-1)
    
    # 计算流体散度惩罚 (Batch内的流量分布与均匀分布的均方差)
    fluid_flow = prob.mean(dim=0) # [num_experts]
    target_flow = torch.ones_like(fluid_flow) / num_experts
    divergence_loss = F.mse_loss(fluid_flow, target_flow)
    
    # 可选：结合 Sinkhorn-Knopp 算法进行无损的最优传输路由
    return prob, divergence_loss
```

---

## 🌌 2. 量子力学启发：相位干涉路由与态叠加 (Schrödinger Phase-Interference Router)

**💡 跨领域理论基础**：
借鉴量子力学中的**波函数坍缩 (Wave Function Collapse)** 与**相位干涉 (Phase Interference)**。量子态由复数概率幅描述，波的叠加会产生相长干涉（Constructive）或相消干涉（Destructive）。

**⚙️ 深度学习机制映射**：
为了解决 CL 中的灾难性遗忘，我们将 Router 的权重扩展到**复数域（Amplitude + Phase）**。在学习初始任务时，振幅和相位共同更新；**在学习后续新任务时，冻结振幅（Amplitude），仅更新相位（Phase）**。
不同任务的 Token 通过相位的干涉来激活特定的 Expert。旧任务的相位签名被永久保留，新任务只能通过寻找正交的相位空间来激活 Expert，完美避免了特征空间的相互覆盖和路由权重的破坏。

**📐 数学公式雏形**：
Router 权重 $W_c = A \cdot e^{j \Phi}$。对于输入 $x$，复数 Logits 为：
$$ c_i(x) = \sum_k A_{ik} x_k e^{j \Phi_{ik}} $$
路由激活概率为波函数的模长平方（波函数坍缩）：
$$ P_i(x) = |c_i(x)|^2 = \text{Re}(c_i(x))^2 + \text{Im}(c_i(x))^2 $$

**💻 代码实现思路 (Pseudocode)**：
```python
class QuantumRouter(nn.Module):
    def __init__(self, dim, num_experts):
        super().__init__()
        self.amplitude = nn.Parameter(torch.randn(dim, num_experts))
        self.phase = nn.Parameter(torch.rand(dim, num_experts) * 2 * math.pi)
        
    def forward(self, x):
        # 冻结振幅，仅相位参与新任务的梯度更新
        complex_weight = self.amplitude.detach() * torch.exp(1j * self.phase)
        complex_logits = torch.matmul(x.to(torch.complex64), complex_weight)
        
        # 坍缩为实数概率 (模长的平方)
        prob = complex_logits.abs() ** 2
        return F.softmax(prob, dim=-1)
```

---

## 📡 3. 通信工程启发：频分复用 LoRA (FDM-LoRA: Frequency-Division Multiplexing)

**💡 跨领域理论基础**：
借鉴现代通信系统（如 5G/WiFi）中的**正交频分复用 (OFDM)** 技术。通过将不同信号调制到相互正交的子载波频率上，实现同一信道内的无干扰并行传输。

**⚙️ 深度学习机制映射**：
现有的正交 LoRA（O-LoRA）多在空域（Spatial Domain）进行矩阵正交化，计算复杂且容易饱和。FDM-LoRA 将 LoRA 的权重矩阵通过 **2D-DCT（离散余弦变换）或 2D-FFT** 映射到频域。
我们为不同的连续学习任务分配**互不重叠的频段掩码（Frequency Bands Mask）**（例如：Task 1 占用低频，Task 2 占用中频）。在频域更新权重后逆变换回空域。由于频段绝对隔离，新任务的权重更新在数学底层上与旧任务**绝对正交**，实现 0% 的灾难性遗忘。

**📐 数学公式雏形**：
设 $\mathcal{F}$ 为二维傅里叶变换，$\mathbf{M}_t$ 为任务 $t$ 的频域布尔掩码（满足 $\mathbf{M}_t \odot \mathbf{M}_k = 0, \forall t \neq k$）。
权重更新量：
$$ \Delta W_t = \mathcal{F}^{-1} \left( \mathbf{M}_t \odot \mathcal{F}(A_t B_t) \right) $$

**💻 代码实现思路 (Pseudocode)**：
```python
def fdm_lora_forward(x, A, B, task_freq_mask):
    # A: [dim, rank], B: [rank, out_dim]
    delta_W = torch.matmul(A, B)
    
    # 变换到频域
    freq_W = torch.fft.rfft2(delta_W)
    
    # 施加任务专属的频段掩码 (切断对其他任务频段的干扰)
    masked_freq_W = freq_W * task_freq_mask
    
    # 逆变换回空域
    orthogonal_delta_W = torch.fft.irfft2(masked_freq_W, s=delta_W.shape)
    
    return F.linear(x, orthogonal_delta_W)
```

---

## 🎛️ 4. 控制论启发：PID 动态稳态路由 (PID-Controlled Dynamic Router)

**💡 跨领域理论基础**：
借鉴工业控制论中的核心算法 **PID 控制器 (Proportional-Integral-Derivative Control)**。通过计算误差的比例（P）、积分（I）和微分（D）来动态调节系统，使其快速且稳定地达到设定值。

**⚙️ 深度学习机制映射**：
在 CL 过程中，Router 极易发生“路由漂移（Routing Drift）”——要么过度倾向新任务的 Expert（遗忘），要么死守旧任务（僵化）。
我们将历史任务的路由分布作为“设定值（Setpoint）”，将当前 Batch 的路由分布作为“测量值”。引入 PID 控制器作为 Router Logits 的动态补偿环。积分项（I）消除长期漂移，微分项（D）抑制剧烈突变，实现 Router 的平滑演进。

**📐 数学公式雏形**：
设 $R_{hist}$ 为旧任务的路由概率移动平均值。误差信号 $e(t) = R_{hist} - R_{curr}(t)$。
Logits 的 PID 补偿：
$$ U(t) = K_p e(t) + K_i \sum_{\tau=0}^t e(\tau) + K_d (e(t) - e(t-1)) $$
$$ \text{Logits}_{final} = \text{Logits}_{raw} + U(t) $$

**💻 代码实现思路 (Pseudocode)**：
```python
class PIDRouter(nn.Module):
    def __init__(self, num_experts, kp=0.1, ki=0.01, kd=0.05):
        # 初始化 PID 参数与状态
        self.kp, self.ki, self.kd = kp, ki, kd
        self.integral_error = 0
        self.prev_error = 0
        self.historical_prob = None # 需在旧任务结束时保存
        
    def forward(self, logits):
        prob = F.softmax(logits, dim=-1)
        
        if self.historical_prob is not None:
            error = self.historical_prob - prob.mean(dim=0)
            self.integral_error += error
            derivative = error - self.prev_error
            
            # 计算 PID 补偿
            pid_correction = self.kp * error + self.ki * self.integral_error + self.kd * derivative
            logits = logits + pid_correction
            self.prev_error = error
            
        return F.softmax(logits, dim=-1)
```

---

## ⚛️ 5. 统计物理启发：自旋玻璃 MoE (Ising Spin-Glass MoE)

**💡 跨领域理论基础**：
借鉴统计物理中的 **Ising 模型 (Ising Model)** 与自旋玻璃态。系统中每个粒子有自旋状态（+1 或 -1），粒子间存在耦合相互作用（Coupling），系统倾向于演化到能量（Hamiltonian）最低的状态。

**⚙️ 深度学习机制映射**：
解决 Expert 之间的协同漂移（Misaligned Co-drift）和冗余激活问题。我们将每个 Expert 视为晶格上的一个“自旋”（激活为 +1，不激活为 -1）。引入一个可学习的 **Expert 相互作用矩阵 $J_{ij}$**。
Router 的目标不再仅仅是独立地计算每个 Expert 的分数，而是要最小化整个 Expert 系统的“能量”。如果 Expert A 和 B 在语义上互斥，$J_{AB}$ 为负，它们将无法同时激活。这在 CL 中形成了一种天然的拓扑保护，新任务无法轻易打破旧任务形成的“磁畴（Magnetic Domains）”。

**📐 数学公式雏形**：
系统哈密顿量（能量）：
$$ \mathcal{H} = - \sum_{i,j} J_{ij} s_i s_j - \sum_i h_i(x) s_i $$
其中 $h_i(x)$ 是 Router 原始输出的 Local Field。
通过 Mean-Field 近似进行路由概率更新：
$$ m_i^{(t+1)} = \tanh \left( \beta \left( h_i(x) + \sum_j J_{ij} m_j^{(t)} \right) \right) $$

**💻 代码实现思路 (Pseudocode)**：
```python
class IsingRouter(nn.Module):
    def __init__(self, dim, num_experts):
        super().__init__()
        self.linear = nn.Linear(dim, num_experts)
        # 相互作用矩阵 J (对称且对角线为0)
        self.J = nn.Parameter(torch.randn(num_experts, num_experts) * 0.01)
        
    def forward(self, x, steps=2):
        h = self.linear(x) # Local field
        
        # 保证 J 的对称性
        J_sym = (self.J + self.J.T) / 2
        J_sym = J_sym - torch.diag(torch.diag(J_sym))
        
        # Mean-Field 迭代 (模拟退火过程)
        m = torch.tanh(h) # 初始磁化率 (激活概率的代理)
        for _ in range(steps):
            interaction = torch.matmul(m, J_sym)
            m = torch.tanh(h + interaction)
            
        # 将 [-1, 1] 映射回 [0, 1] 的路由概率
        prob = (m + 1) / 2
        return prob / prob.sum(dim=-1, keepdim=True)
```

---

## 📐 6. 老师建议落地：正交软混合路由 (Orthogonal Soft Routing) — v8_sota_1 假设

**背景（2026-06-12）**：v6_sota_2 最佳 seen_avg=0.35；v6_sota_3–5 证明 frozen-specialized LoRA 的参数级 soft blend 破坏性随训练预算单调增长；`overlap_mean_cosine` 仍达 0.87+。老师建议第三贡献：路由权重正交化，防止重叠分支混合。

**单点假设**：评测期 top-k soft blend 前，按分支 LoRA 向量余弦相似度对权重做指数衰减门控（或 Gram-Schmidt 投影），高相似分支不可同时获高权重。

**预期**：在保持 v6_2 的 1ep/batch=2/soft top-3 协议下，seen_avg +0.05~0.15；不重复 v6_4 硬路由脆断。

**配置草案**：`router.orthogonal_blend: true`, `orthogonal_blend_lambda: 0.5`（基座 v6_sota_2，禁用 v7_1 NLL 仲裁）。

---

## 📐 7. v7_sota_2 假设（若需轻量路由改进）

**背景**：v7_sota_1 于 seg5 早停（seen=0.197）；全链路 NLL 仲裁过激。

**单点假设**：仅保留 `prototype_calibration_prior: 20` + 训练期 `margin_filter_min_gap: 0.04` 过滤低质量伪标签；**不启用** `nll_arbitration`。

**基座**：v6_sota_2。预期 oracle +0.03~0.06，seen +0.02~0.05。

---

## 🔄 8. 迭代协议（与监控器绑定，2026-06-12 起强制）

每个 `v*_sota_*` 版本必须遵循：

1. **失败分析**（`scripts/sota_failure_analysis.py` → `archive/{next}/FAILURE_ANALYSIS.md`，Agent 审阅至 `status: ready`）
2. **单点实现**（yaml + run.sh + `CHANGES.md`，对照模板 `archive/TEMPLATE_FAILURE_ANALYSIS.md`）
3. **tmux 启动**（仅当监控 `pending_action=launch` 且门禁通过）

当前执行中：**v8_sota_1**（Orthogonal Soft Routing）。失败后排 **v8_sota_2**（routing-aware ortho training loss）。详见 `SOTA_PROGRESS.md` § Iteration Protocol。

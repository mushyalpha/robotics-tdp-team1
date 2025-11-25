#Cause the motion graph is difficult to see the track
#So I divided it into 4 sub graph, just see the subplot

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

path="./balance_controller/StandUpFromFront.motion"
output_dir=os.path.join(os.path.dirname(path),"figures")

df = pd.read_csv(path, comment='#', header=None)

with open(path, 'r', encoding='utf-8') as f:
    header_line = f.readline().strip()
columns = header_line.split(',')[2:]  
df.columns = ['time', 'pose'] + columns

print("columes value:", len(df.columns))
print("some example data:")
print(df.head())

#turn the time to ms
def time_to_ms(t):
    h, m, s = t.split(':')
    return int(h) * 3600000 + int(m) * 60000 + int(float(s) * 1000)

df['time_ms'] = df['time'].apply(lambda t: time_to_ms(t))

# plot
groups = {
    "Arms": ["RShoulderPitch","RShoulderRoll","RElbowYaw","RElbowRoll",
             "LShoulderPitch","LShoulderRoll","LElbowYaw","LElbowRoll"],
    "Hips": ["RHipYawPitch","LHipYawPitch","RHipRoll","LHipRoll","RHipPitch","LHipPitch"],
    "Knees": ["RKneePitch","LKneePitch"],
    "Ankles": ["RAnklePitch","LAnklePitch","RAnkleRoll","LAnkleRoll"],
}

colors = plt.cm.tab20(np.linspace(0, 1, 20))

# plot the whole motion track
fig, axes = plt.subplots(len(groups), 1, figsize=(12, 30), sharex=True)
fig.suptitle("Grouped Joint Motion (Offset Display by Body Part)", fontsize=14)

for ax, (group_name, joints) in zip(axes, groups.items()):
    if not joints:
        ax.axis('off')
        continue
    
    offset = 0
    for i, j in enumerate(joints):
        if j not in df.columns:
            continue
        ax.plot(df['time_ms'], df[j] + offset, label=j, color=colors[i % len(colors)], linewidth=1.0)
        offset += 2  # 每个关节向上错开
    
    ax.set_title(group_name, fontsize=11, loc='left', pad=5)
    ax.set_ylabel("Angle (rad, offset)")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7, ncol=3, loc='center left',bbox_to_anchor=(1.02, 0.5))

axes[-1].set_xlabel("Time (ms)")
plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig(os.path.join(output_dir, "motion_overview.png"), dpi=300)
plt.show()

#plot the sub graph
for group_name, joints in groups.items():
    if not joints:
        continue
    i=1
    plt.figure(figsize=(10, 6))
    offset = 0
    for i, j in enumerate(joints):
        if j not in df.columns:
            continue
        plt.plot(df['time_ms'], df[j] + offset, label=j,
                 color=colors[i % len(colors)], linewidth=1.0)
        offset += 3

    plt.title(f"{group_name} Joint Motion (Offset Display)", fontsize=13)
    plt.xlabel("Time (ms)")
    plt.ylabel("Angle (rad, offset)")
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=8, ncol=3, loc='center left',bbox_to_anchor=(1.02, 0.5))
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"motion_subplot{i}.png"), dpi=300)
    i=i+1
    plt.show()

from controller import Supervisor
from pathlib import Path
from datetime import datetime
import csv
import json
import yaml


def main():
    supervisor = Supervisor()
    time_step = int(supervisor.getBasicTimeStep())

    # Test configuration
    ROBOT_DEF_NAME = "NAO"   # must match DEF name in your .wbt world

    # Frequencies to test [Hz]
    TEST_FREQUENCIES = [0.1, 0.5, 0.8, 1., 1.2, 1.3, 1.4, 1.45, 1.5, 1.55]

    # Duration of each trial [s]
    SIM_DURATION = 20.0

    # Axes mapping for this world:
    FORWARD_AXIS = "x"
    DRIFT_AXIS = "y"
    HEIGHT_AXIS = "z"

    # Height-based failure threshold used during analysis
    HEIGHT_FAILURE_THRESHOLD = 0.15  # [m], for z

    # Starting pose
    INITIAL_TRANSLATION = [2.53, 0, 0.32]
    INITIAL_ROTATION = [0.0, 0.0, 1.0, 3.14]

    # CSV file name (inside the experiment directory)
    CSV_FILENAME = "batch_measurements_full.csv"

    # Webots node handles
    robot_node = supervisor.getFromDef(ROBOT_DEF_NAME)
    if robot_node is None:
        print(f"[ERROR] Could not find robot with DEF name '{ROBOT_DEF_NAME}'")
        return

    translation_field = robot_node.getField("translation")
    rotation_field = robot_node.getField("rotation")
    custom_data_field = robot_node.getField("customData")

    # Experiment details for metadata
    # Root directory for all experiments (relative to current working dir)
    EXPERIMENTS_ROOT = Path("../../controller-testing/walking-controller-tests")
    EXPERIMENTS_ROOT.mkdir(parents=True, exist_ok=True)

    # Unique experiment ID and directory
    now = datetime.now()
    experiment_id = f"nao_freq_sweep_{now.strftime('%Y%m%d_%H%M%S')}"
    OUTPUT_DIR = EXPERIMENTS_ROOT / experiment_id
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = OUTPUT_DIR / CSV_FILENAME
    metadata_path = OUTPUT_DIR / "metadata.yaml"

    print(f"[INFO] Experiment ID: {experiment_id}")
    print(f"[INFO] Output directory: {OUTPUT_DIR}")
    print(f"[INFO] CSV path: {csv_path}")

    # Build metadata structure
    metadata = {
        "experiment_id": experiment_id,
        "timestamp": now.isoformat(),
        "robot": {
            "def_name": ROBOT_DEF_NAME,
            "type": "NAO",
            "controller": "WalkingMin",
            "gait_templates": {
                "start": "motor_patterns_smooth_start.csv",
                "walk": "motor_patterns_continous_gait.csv",
                "stop": "motor_patterns_smooth_stop.csv",
            },
        },
        "simulation": {
            # Fill these manually
            "webots_version": "R2025a",
            "world_file": "WP2_single-robot-controller-test.wbt)",
            "basic_time_step_ms": time_step,
            "notes": "",
        },
        "protocol": {
            "test_type": "frequency_sweep_time_based",
            "frequencies_hz": TEST_FREQUENCIES,
            "sim_duration_s": SIM_DURATION,
            "axes": {
                "forward": FORWARD_AXIS,
                "drift": DRIFT_AXIS,
                "height": HEIGHT_AXIS,
            },
            "failure_criterion": {
                "type": "height_threshold",
                "height_axis": HEIGHT_AXIS,
                "threshold_m": HEIGHT_FAILURE_THRESHOLD,
                "description": "Trial fails if min(z) < threshold at any time.",
            },
        },
        "logging": {
            "directory": str(OUTPUT_DIR),
            "csv_file": CSV_FILENAME,
            "columns": [
                "trial_index",
                "step_frequency",
                "t_abs",
                "t_rel",
                "x",
                "y",
                "z",
                "rot_x",
                "rot_y",
                "rot_z",
                "rot_angle",
            ],
        },
    }

    # Write metadata.yaml
    with open(metadata_path, "w") as f:
        yaml.dump(metadata, f, sort_keys=False)
    print(f"[INFO] Wrote metadata: {metadata_path}")

    # Main batch run
    with open(csv_path, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)

        # Header: one row per timestep per trial
        writer.writerow([
            "trial_index",
            "step_frequency",
            "t_abs",
            "t_rel",
            "x", "y", "z",
            "rot_x", "rot_y", "rot_z", "rot_angle",
        ])

        # Warm-up to let devices initialize
        for _ in range(10):
            supervisor.step(time_step)

        # Iterate trials
        for trial_index, freq in enumerate(TEST_FREQUENCIES):
            print(f"[INFO] Starting trial {trial_index} at {freq} Hz")

            # 1) Reset robot pose & physics
            translation_field.setSFVec3f(INITIAL_TRANSLATION)
            rotation_field.setSFRotation(INITIAL_ROTATION)
            supervisor.simulationResetPhysics()

            # Let things settle for a few steps
            for _ in range(5):
                supervisor.step(time_step)

            # 2) Update WalkingMin parameters via customData
            # Large target_distance so its distance-based stopping won't trigger
            config = {
                "step_frequency": freq,
                "target_distance": 1e6,
            }
            custom_data_field.setSFString(json.dumps(config))

            # 3) Start measurement
            start_time = supervisor.getTime()

            # 4) Run for fixed duration, logging every timestep
            while supervisor.step(time_step) != -1:
                t_abs = supervisor.getTime()
                t_rel = t_abs - start_time
                if t_rel > SIM_DURATION:
                    break

                pos = translation_field.getSFVec3f()
                rot = rotation_field.getSFRotation()

                writer.writerow([
                    trial_index,
                    freq,
                    t_abs,
                    t_rel,
                    pos[0], pos[1], pos[2],
                    rot[0], rot[1], rot[2], rot[3],
                ])

            print(f"[INFO] Finished trial {trial_index} at {freq} Hz")

        print("[INFO] All trials completed.")
        print(f"[INFO] Data and metadata available in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()



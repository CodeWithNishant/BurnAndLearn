# train_agent.py
import os
import argparse
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback, StopTrainingOnRewardThreshold
import gymnasium as gym
import numpy as np
from burn_and_learn_gym import RocketEnv

def make_env(seed=None):
    def _init():
        env = RocketEnv()
        env = Monitor(env)  # Monitor first
        if seed is not None:
            # modern seeding: reset with seed
            env.reset(seed=seed)
        return env
    return _init

def main(args):
    # --- dirs ---
    run_id = args.run_id or "run"
    base_dir = os.path.join("runs", run_id)
    os.makedirs(base_dir, exist_ok=True)
    models_dir = os.path.join(base_dir, "models")
    logs_dir = os.path.join(base_dir, "tb_logs")
    eval_dir = os.path.join(base_dir, "eval")
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(eval_dir, exist_ok=True)

    # --- envs ---
    n_envs = args.n_envs
    # vec_env = DummyVecEnv([make_env(seed=1000 + i) for i in range(n_envs)])
    vec_env = SubprocVecEnv([make_env(seed=1000 + i) for i in range(n_envs)])

    # --- evaluation env (single env) ---
    eval_env = SubprocVecEnv([make_env(seed=9999)])

    # --- callbacks ---
    # Save checkpoints periodically
    checkpoint_cb = CheckpointCallback(save_freq=args.checkpoint_freq,
                                       save_path=models_dir,
                                       name_prefix="burnlearn")

    # Stop training when achieved a reward threshold on eval
    # stop_cb = StopTrainingOnRewardThreshold(reward_threshold=args.stop_reward, verbose=1)

    # Eval + keep best model
    eval_cb = EvalCallback(eval_env,
                           best_model_save_path=os.path.join(models_dir, "best"),
                           log_path=eval_dir,
                           eval_freq=args.eval_freq,
                           deterministic=True,
                           render=False,
                        #    callback_after_eval=stop_cb
                           )

    # --- model ---
    policy_kwargs = dict(net_arch=[dict(pi=[256, 256], vf=[256, 256])])
    model = PPO("MlpPolicy",
                vec_env,
                verbose=1,
                tensorboard_log=logs_dir,
                n_steps=args.n_steps,
                batch_size=args.batch_size,
                learning_rate=args.learning_rate,
                policy_kwargs=policy_kwargs,
                seed=42)

    # --- train ---
    total_timesteps = args.timesteps
    model.learn(total_timesteps=total_timesteps, callback=[checkpoint_cb, eval_cb])

    # --- save final ---
    final_path = os.path.join(models_dir, "final_model.zip")
    model.save(final_path)
    print(f"Training finished. Final model saved to: {final_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=200_000, help="Total training timesteps")
    parser.add_argument("--n-envs", type=int, default=8, dest="n_envs")
    parser.add_argument("--run-id", type=str, default=None)
    parser.add_argument("--checkpoint-freq", type=int, default=100_000)
    parser.add_argument("--eval-freq", type=int, default=5000)
    parser.add_argument("--stop-reward", type=float, default=800.0)
    parser.add_argument("--n-steps", type=int, default=2048)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    args = parser.parse_args()
    main(args)
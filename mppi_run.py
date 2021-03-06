"""

Chen Liang, Beihang University
Code accompanying the paper
"Learing to guide: Guidance Law Based on Deep Meta-learning and Model Predictive Path Integral Control"


"""

import numpy as np

from neural_dynamics_dense import dense_dynamics_model
from mppi_controller import mpc_controller

from cost_functions import missile_costfn
from missile_env import missile_env



def run( env,
         cost_fn,
         num_simulated_paths=1000,
         mpc_horizon=1,
         iter = 1,
         ):

    """

    Arguments:

    env                         The missile guidance environment.

    cost_fn                     Cost function for missile guidance which is detailed in
    |_                          remark 2 and 3 in the manuscript.

    learning_rate_alpha         The learning rate for meta-learning online adaptive control.

    num_simulated_paths         Number of paths/trajectories/rollouts generated by the
    |                           model predictive path integral(MPPI) controller to give an action.
    |_                          We use these to sample,detailed at the manuscript.

    mpc_horizon                 The horizon of the MPPI controller.

    iter                        The No. for this test run of guidance.

    """
    #========================================================
    #
    # init neural dynamic model
    dyn_model = dense_dynamics_model(env = env)

    #========================================================
    #
    # init MPPI controller
    controller = mpc_controller(env=env,
                                            dyn_model=dyn_model,
                                            horizon=mpc_horizon,
                                            cost_fn=cost_fn,
                                            num_simulated_paths=num_simulated_paths)


    #========================================================
    #
    # To randomize the environment.
    ob = env.reset_recursive()

    #========================================================
    #
    # some preparation.
    controller.init_mppi(ob.reshape((1, ob.shape[0])))
    ob_exp = []
    ac_exp = []
    deltas_exp = []
    next_exp = []
    i = 0

    #act_error = np.array([0.2, 0.2])

    #========================================================
    #
    # The main guidance loop.
    done = False
    while not done:
        i = i + 1

        ac = controller.get_ac_mppi(ob.reshape((1, ob.shape[0])))

        ac = np.clip(ac, -2, 2)

        if i > 600:
            # a simple way to do actuator failure of 50% starting at 3s
            next_ob, done = env.step(0.5 * ac)
        else:
            #
            next_ob, done = env.step(ac)


        print('Dist:{:.2f} theta_l:{:.5f}  phi_l:{:.5f}  D_theta_l:{:.5f} D_phi_l:{:.5f}'.format(next_ob[0] * 1000.0,
                                                                                                 next_ob[3], next_ob[4],
                                                                                                 next_ob[8],
                                                                                                 next_ob[9]))
        ob_exp.append(ob)
        ac_exp.append(ac)
        delta = next_ob - ob
        deltas_exp.append(np.hstack((delta[0:5], delta[8:10])))
        next_exp.append(next_ob)

        if ob_exp.__len__() > 2:
            loss = dyn_model.fit(np.array(ob_exp), np.array(ac_exp), np.array(deltas_exp), np.array(next_exp))
            print('Online adaption loss:{:.10f}'.format(loss))

        if ob_exp.__len__() > 15:
            del ob_exp[0]
            del ac_exp[0]
            del deltas_exp[0]
            del next_exp[0]

        ob = next_ob


def main():

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('--simulated_paths', '-sp', type=int, default=1000)
    parser.add_argument('--mpc_horizon', '-m', type=int, default=1)
    parser.add_argument('--iter_num', type=int, default=1)# This set the file number of saved data.
    args = parser.parse_args()

    # Make env

    env = missile_env(num_index= args.iter_num)
    cost_fn = missile_costfn

    # run
    run(env=env,
        cost_fn=cost_fn,
        num_simulated_paths=args.simulated_paths,
        mpc_horizon=args.mpc_horizon,
        iter=args.iter_num,
        )


if __name__ == "__main__":
    main()

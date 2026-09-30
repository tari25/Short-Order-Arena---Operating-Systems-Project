"""Your scheduler. Edit this file.

Everything you write goes in here. A submission is one file of code - extra
.py files next to it are not importable when the server loads your scheduler,
so they are rejected rather than silently ignored.

This is a working scheduler, so you can run it right now and see numbers:

    START.cmd play my-scheduler                (Windows)
    ./start.sh play my-scheduler               (macOS and Linux)

It is called `idiot_sandwich` because it is one. Whenever a cook is free it
hands them the *biggest* job on the rail - the banquet, the roast, the thing
with six steps - and leaves the espressos and the salads standing. Worse, the
moment something even bigger turns up it drags a cook off what they were doing
and starts that instead, paying a context switch to make a worse decision. It
never checks whether a customer is still going to be there at the end, and
never once wonders whether that was a sensible dish to have started.

Run it and watch the dining room empty. Then look at which orders walked out
and ask what order you would have cooked them in. That question is the
assignment; the rest of this file is the equipment.

The picture: cooks are CPU cores, orders are processes, a recipe's `work`
steps are CPU bursts and its `wait` steps (the oven) are I/O bursts. You are
the scheduler. The engine calls `schedule` at every scheduling point - service
opening, an order arriving, a cook coming free, an order coming back from the
oven, a customer walking out, or an alarm you set - and you say which order
each cook should be working on. Every time a cook takes on an order it pays a
context switch of `obs.kitchen.switch_cost` ticks, so changing your mind is
not free.

There is a second resource. Every work step happens at a **station** - the
prep bench, the pass, the bar - and only so many cooks fit at each: a lock
with a fixed number of permits. Assigning an order whose station is full is
refused, and the cook you meant to use just stands there. `fill_idle` below
counts places for you; the moment you write your own loop, you have to. Look
at `obs.stations` and `obs.free_stations()`, and check `invalid assignments`
in the report - if it is not zero, you are dropping cooks on the floor.

You are marked on five things: how many customers you serve before they walk
out, how quickly an order first gets a cook, how long orders take relative to
the work in them, how much time you burn switching, and how evenly the wait is
shared. `python -m kitchen.cli play` prints all five.

The reference schedulers are named after kitchen characters -
`middle_management`, `headless_chicken`, `julia_child`, `sous_chef`,
`stickler`, `trainee`, `portion_control`, `smoke_break` - and
`gordon_ramsay` is the one to beat. The names say nothing about the
algorithms; `baselines` prints what each one implements. Each one's
description names the textbook algorithm it implements, and those textbook
names work too, so `play sjf` and `play julia_child` are the same scheduler.
`baselines` lists them all.

The full API is in the student guide that came with this download. Useful
things to know about `obs`:

    obs.time                  now, in ticks
    obs.reason.kinds          why you were called
    obs.ready                 orders waiting for a cook, oldest first
    obs.runnable              the same, minus the ones whose station is full
    obs.idle_cores            cooks with nothing to do
    obs.working_cores         cooks mid-order (core.order is the order id)
    obs.stations              each station: name, capacity, busy, free
    obs.free_stations()       {name: places free}, a dict you spend as you assign
    obs.can_start(order)      is there a place at the station this order needs?
    order.station             where its current step happens (None for a wait)
    order.work_remaining      ticks of work left (None if durations are hidden)
    order.time_left           ticks until the customer walks out
    order.priority            1 regular, 2 hurried, 3 VIP
    obs.estimate_remaining(o) a guess at work_remaining when it is hidden

And about `Decision`:

    d.assign(core, order)     put this order on this cook (preempts whatever it held)
    d.idle(core)              take the cook off its order
    d.wake_in(ticks)          call me again in this many ticks (your timer interrupt)
    d.annotate(text=..., queue=[...], tags={...})   drawn by the viewer, ignored by the engine

This file is the whole submission: when you are done, upload it to Moodle.
"""

from kitchen import Decision, Scheduler, fill_idle


class MyScheduler(Scheduler):
    name = "better_sandwhich"
    version = "1"

    def reset(self, seed):
        pass

    def schedule(self, obs):
        est = obs.estimate_remaining

        #sjf
        rail = sorted(
            (o for o in obs.ready if est(o) <= o.time_left), 
            # estimated work time against customers patience
            # takes only those where the work time is less than the patience
            key=est,
        )

        decision = Decision()
        fill_idle(decision, obs, rail) #gives tasks to idle cooks

        return decision.annotate(
            text=f"{len(obs.ready)} on the rail, shortest first",
            queue=[o.id for o in rail],
        )
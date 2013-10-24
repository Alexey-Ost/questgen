# coding: utf-8
import itertools

from questgen.quests.base_quest import QuestBetween2, ROLES, RESULTS
from questgen import facts
from questgen import logic


class Help(QuestBetween2):
    TYPE = 'help'
    TAGS = ('can_start', 'has_subquests', 'can_continue')

    @classmethod
    def construct(cls, nesting, selector, initiator, initiator_position, receiver, receiver_position):

        hero = selector.heroes()[0]

        ns = selector._kb.get_next_ns()

        start = facts.Start(uid=ns+'start',
                            type=cls.TYPE,
                            nesting=nesting,
                            description=u'Начало: помочь знакомому',
                            require=[facts.LocatedIn(object=hero.uid, place=initiator_position.uid),
                                     facts.LocatedIn(object=receiver.uid, place=receiver_position.uid)],
                            actions=[facts.Message(type='intro')])

        participants = [facts.QuestParticipant(start=start.uid, participant=initiator.uid, role=ROLES.INITIATOR),
                        facts.QuestParticipant(start=start.uid, participant=receiver.uid, role=ROLES.RECEIVER) ]

        finish_successed = facts.Finish(uid=ns+'finish_successed',
                                        result=RESULTS.SUCCESSED,
                                        nesting=nesting,
                                        description=u'помощь оказана',
                                        require=[facts.LocatedIn(object=hero.uid, place=initiator_position.uid)],
                                        actions=[facts.GiveReward(object=hero.uid, type='finish_successed'),
                                                 facts.GivePower(object=initiator.uid, power=1),
                                                 facts.GivePower(object=receiver.uid, power=1)])

        finish_failed = facts.Finish(uid=ns+'finish_failed',
                                     result=RESULTS.FAILED,
                                     nesting=nesting,
                                     description=u'не удалось помочь',
                                     actions=[facts.GiveReward(object=hero.uid, type='finish_failed'),
                                              facts.GivePower(object=initiator.uid, power=-1),
                                              facts.GivePower(object=receiver.uid, power=-1)])

        help_quest = selector.create_quest_from_person(nesting=nesting+1, initiator=receiver, tags=('can_continue',))
        help_extra = []

        for help_fact in logic.filter_subquest(help_quest, nesting):
            if isinstance(help_fact, facts.Start):
                help_extra.append(facts.Jump(state_from=start.uid, state_to=help_fact.uid, start_actions=[facts.Message(type='before_help')]))
            elif isinstance(help_fact, facts.Finish):
                if help_fact.result == RESULTS.SUCCESSED:
                    help_extra.append(facts.Jump(state_from=help_fact.uid, state_to=finish_successed.uid, start_actions=[facts.Message(type='after_successed_help')]))
                else:
                    help_extra.append(facts.Jump(state_from=help_fact.uid, state_to=finish_failed.uid))

        subquest = facts.SubQuest(uid=ns+'help_subquest', members=logic.get_subquest_members(itertools.chain(help_quest, help_extra)))

        line = [ start,
                 finish_successed,
                 finish_failed,
                 subquest ]

        line.extend(participants)
        line.extend(help_quest)
        line.extend(help_extra)

        return line
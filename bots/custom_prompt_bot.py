# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from datetime import datetime
from botbuilder.ai.qna import QnAMaker, QnAMakerEndpoint
from recognizers_number import recognize_number, Culture
from recognizers_date_time import recognize_datetime

from botbuilder.core import (
    ActivityHandler,
    ConversationState,
    TurnContext,
    UserState,
    MessageFactory,
    CardFactory,
)
from botbuilder.schema import (
    ChannelAccount,
    HeroCard,
    CardImage,
    CardAction,
    ActionTypes,
    Activity,
    ActivityTypes,
    SuggestedActions,
)

from data_models import ConversationFlow, Question, Question2, UserProfile, State,Slot,NoMeetingPeriod,Transportation


class ValidationResult:
    def __init__(
        self, is_valid: bool = False, value: object = None, message: str = None
    ):
        self.is_valid = is_valid
        self.value = value
        self.message = message


class CustomPromptBot(ActivityHandler):
    def __init__(self, config, conversation_state: ConversationState, user_state: UserState):
        if conversation_state is None:
            raise TypeError(
                "[CustomPromptBot]: Missing parameter. conversation_state is required but None was given"
            )
        if user_state is None:
            raise TypeError(
                "[CustomPromptBot]: Missing parameter. user_state is required but None was given"
            )

        self.conversation_state = conversation_state
        self.user_state = user_state

        self.flow_accessor = self.conversation_state.create_property("ConversationFlow")
        self.profile_accessor = self.user_state.create_property("UserProfile")
        self.qna_maker = QnAMaker(
            QnAMakerEndpoint(
                knowledge_base_id=config.QNA_KNOWLEDGEBASE_ID,
                endpoint_key=config.QNA_ENDPOINT_KEY,
                host=config.QNA_ENDPOINT_HOST,
            )

        )

    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)

        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    async def on_members_added_activity(
            self, members_added: [ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    f"Welcome to Meeting Assistant Bot. I will introduce "
                    f"you how to use it. First please fill in your information and upload your calendar."
                )
                await self._send_welcome_message(turn_context)

    async def _send_welcome_message(self, turn_context: TurnContext):
        card = HeroCard(
            text="You can find introduction and complete your personal information",
            buttons=[
                CardAction(
                    type=ActionTypes.im_back, title="1. User profile", value="Choice1"
                ),
                CardAction(
                    type=ActionTypes.im_back, title="2. Personal preference", value="Choice2"
                ),
                CardAction(
                    type=ActionTypes.im_back, title="3. Upload calender file", value="Choice3"
                ),
                CardAction(
                    type=ActionTypes.im_back, title="4. help", value="Choice4"
                ),
            ],
        )

        reply = MessageFactory.attachment(CardFactory.hero_card(card))
        await turn_context.send_activity(reply)


    async def on_message_activity(self, turn_context: TurnContext):
        if (
            turn_context.activity.attachments
            and len(turn_context.activity.attachments) > 0
        ):
            await self._handle_incoming_attachment(turn_context)
        else:
            await self._handle_user_info(turn_context)

        # await self._send_welcome_message(turn_context)

        # Get the state properties from the turn context.
        # profile = await self.profile_accessor.get(turn_context, UserProfile)
        # flow = await self.flow_accessor.get(turn_context, ConversationFlow)
        #
        # await self._fill_out_user_profile(flow, profile, turn_context)

    async def _handle_incoming_attachment(self, turn_context: TurnContext):
        await turn_context.send_activity("you have send a file.")

    async def _handle_user_info(self, turn_context: TurnContext):

        reply = Activity(type=ActivityTypes.message)
        profile = await self.profile_accessor.get(turn_context, UserProfile)
        flow = await self.flow_accessor.get(turn_context, ConversationFlow)

        if flow.CalenderState == State.NONE:
            mess = turn_context.activity.text
            if mess == "Choice1":
                # reply.text = "This is user profile section."
                flow.CalenderState = State.PROFILE
                await turn_context.send_activity("This is user profile section.")
                await self._fill_out_user_profile(flow, profile, turn_context)
            elif mess == "Choice2":
                # reply.text = "This is personal preference section."
                flow.CalenderState = State.PREFERENCE
                await turn_context.send_activity("This is personal preference section.")
                await self._fill_out_personal_preference(flow, profile, turn_context)
                # await self.test(flow, profile, turn_context)
            elif mess == "Choice3":
                # reply.text = "This is an uploaded attachment."
                flow.CalenderState = State.FILE
                await turn_context.send_activity("This is uploaded attachment.")
            else:
                response = await self.qna_maker.get_answers(turn_context)
                if response and len(response) > 0:
                    await turn_context.send_activity(MessageFactory.text(response[0].answer))
                else:
                    await turn_context.send_activity("No QnA Maker answers were found.")

                await self._send_welcome_message(turn_context)
            # await turn_context.send_activity(reply)

        elif flow.CalenderState == State.PROFILE:
            await self._fill_out_user_profile(flow, profile, turn_context)

        elif flow.CalenderState == State.PREFERENCE:
            # await turn_context.send_activity("personal preference state")
            await self._fill_out_personal_preference(flow, profile, turn_context)
            # await self.test(flow, profile, turn_context)

        elif flow.CalenderState == State.FILE:
            await turn_context.send_activity("upload file state")
        elif flow.CalenderState == State.HELP:
            await turn_context.send_activity("help state")

    async def _fill_out_user_profile(
        self, flow: ConversationFlow, profile: UserProfile, turn_context: TurnContext
    ):
        user_input = turn_context.activity.text.strip()

        # ask for name
        if flow.last_question_asked == Question.NONE:
            await turn_context.send_activity(
                MessageFactory.text("Let's get started. What is your name?")
            )
            flow.last_question_asked = Question.NAME

        # validate name then ask for age
        elif flow.last_question_asked == Question.NAME:
            validate_result = self._validate_name(user_input)
            if not validate_result.is_valid:
                await turn_context.send_activity(
                    MessageFactory.text(validate_result.message)
                )
            else:
                profile.name = validate_result.value
                await turn_context.send_activity(
                    MessageFactory.text(f"Hi {profile.name}")
                )
                await turn_context.send_activity(
                    MessageFactory.text("How old are you?")
                )
                flow.last_question_asked = Question.AGE

        # validate age then ask for date
        elif flow.last_question_asked == Question.AGE:
            validate_result = self._validate_age(user_input)
            if not validate_result.is_valid:
                await turn_context.send_activity(
                    MessageFactory.text(validate_result.message)
                )
            else:
                profile.age = validate_result.value
                await turn_context.send_activity(
                    MessageFactory.text(f"I have your age as {profile.age}.")
                )
                await turn_context.send_activity(
                    MessageFactory.text("what is your address?")
                )
                flow.last_question_asked = Question.ADDR

        # validate date and wrap it up
        elif flow.last_question_asked == Question.ADDR:
            validate_result = self._validate_addr(user_input)
            if not validate_result.is_valid:
                await turn_context.send_activity(
                    MessageFactory.text(validate_result.message)
                )
            else:
                profile.addr = validate_result.value
                await turn_context.send_activity(
                    MessageFactory.text(
                        f"Your address {profile.addr} is saved."
                    )
                )
                await turn_context.send_activity(
                    MessageFactory.text(
                        f"Thanks for completing the booking {profile.name}."
                    )
                )
                await turn_context.send_activity(
                    MessageFactory.text("Type anything to run the bot again.")
                )
                flow.last_question_asked = Question.NONE
                flow.CalenderState = State.NONE

                await self._send_welcome_message(turn_context)

    def _validate_name(self, user_input: str) -> ValidationResult:
        if not user_input:
            return ValidationResult(
                is_valid=False,
                message="Please enter a name that contains at least one character.",
            )

        return ValidationResult(is_valid=True, value=user_input)

    def _validate_age(self, user_input: str) -> ValidationResult:
        # Attempt to convert the Recognizer result to an integer. This works for "a dozen", "twelve", "12", and so on.
        # The recognizer returns a list of potential recognition results, if any.
        results = recognize_number(user_input, Culture.English)
        for result in results:
            if "value" in result.resolution:
                age = int(result.resolution["value"])
                if 18 <= age <= 120:
                    return ValidationResult(is_valid=True, value=age)

        return ValidationResult(
            is_valid=False, message="Please enter an age between 18 and 120."
        )

    def _validate_date(self, user_input: str) -> ValidationResult:
        try:
            # Try to recognize the input as a date-time. This works for responses such as "11/14/2018", "9pm",
            # "tomorrow", "Sunday at 5pm", and so on. The recognizer returns a list of potential recognition results,
            # if any.
            results = recognize_datetime(user_input, Culture.English)
            for result in results:
                for resolution in result.resolution["values"]:
                    if "value" in resolution:
                        now = datetime.now()

                        value = resolution["value"]
                        if resolution["type"] == "date":
                            candidate = datetime.strptime(value, "%Y-%m-%d")
                        elif resolution["type"] == "time":
                            candidate = datetime.strptime(value, "%H:%M:%S")
                            candidate = candidate.replace(
                                year=now.year, month=now.month, day=now.day
                            )
                        else:
                            candidate = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

                        # user response must be more than an hour out
                        diff = candidate - now
                        if diff.total_seconds() >= 3600:
                            return ValidationResult(
                                is_valid=True,
                                value=candidate.strftime("%m/%d/%y"),
                            )

            return ValidationResult(
                is_valid=False,
                message="I'm sorry, please enter a date at least an hour out.",
            )
        except ValueError:
            return ValidationResult(
                is_valid=False,
                message="I'm sorry, I could not interpret that as an appropriate "
                "date. Please enter a date at least an hour out.",
            )

    def _validate_addr(self, user_input: str) -> ValidationResult:
        return ValidationResult(is_valid=True, value=user_input)

    async def test(
            self, flow: ConversationFlow, profile: UserProfile, turn_context: TurnContext
    ):
        reply = MessageFactory.text("What is your favorite color?")

        reply.suggested_actions = SuggestedActions(
            actions=[
                CardAction(title="Red", type=ActionTypes.im_back, value="Red"),
                CardAction(title="Yellow", type=ActionTypes.im_back, value="Yellow"),
                CardAction(title="Blue", type=ActionTypes.im_back, value="Blue"),
            ]
        )

        return await turn_context.send_activity(reply)
    async def _fill_out_personal_preference(
            self, flow: ConversationFlow, profile: UserProfile, turn_context: TurnContext
    ):
        # await turn_context.send_activity("_fill_out_personal_preference")
        user_input = turn_context.activity.text.strip()

        # ask for meeting slot
        if flow.last_question_asked2 == Question2.NONE:
            # await turn_context.send_activity(
            #     MessageFactory.text("Let's get started. Which time slot during meetings do your prefer?")
            # )
            reply = MessageFactory.text("Let's get started. Which time slot during meetings do your prefer?")
            reply.suggested_actions = SuggestedActions(
                actions=[
                    CardAction(title="HALF HOUR", type=ActionTypes.im_back, value="half hour"),
                    CardAction(title="ONE HOUR", type=ActionTypes.im_back, value="one hour"),
                    CardAction(title="TWO HOURS", type=ActionTypes.im_back, value="two hours"),
                    CardAction(title="NONE", type=ActionTypes.im_back, value="none"),
                ]
            )
            flow.last_question_asked2 = Question2.MEETINGSOLT

            return await turn_context.send_activity(reply)

        # validate name then ask for age
        elif flow.last_question_asked2 == Question2.MEETINGSOLT:
            profile.meetingSlot = turn_context.activity.text
            await turn_context.send_activity(
                MessageFactory.text(f"You have selected {profile.meetingSlot} for meeting slot")
            )
            flow.last_question_asked2 = Question2.NOMEETPERIOD
            reply = MessageFactory.text("Next. Which time period you don't want meeting?")
            reply.suggested_actions = SuggestedActions(
                actions=[
                    CardAction(title="before 8am", type=ActionTypes.im_back, value="before 8am"),
                    CardAction(title="during lunch time", type=ActionTypes.im_back, value="during lunch time"),
                    CardAction(title="after 5pm", type=ActionTypes.im_back, value="after 5pm"),
                    CardAction(title="NONE", type=ActionTypes.im_back, value="NONE"),
                ]
            )
            return await turn_context.send_activity(reply)

        # validate age then ask for date
        elif flow.last_question_asked2 == Question2.NOMEETPERIOD:
            profile.nomeetPeriod = turn_context.activity.text
            flow.last_question_asked2 = Question2.TRANSPORTATION
            await turn_context.send_activity(
                MessageFactory.text(f"You have selected {profile.nomeetPeriod} for no meeting period.")
            )
            reply = MessageFactory.text("Next. Which transportation you want to attend meetings?")
            reply.suggested_actions = SuggestedActions(
                actions=[
                    CardAction(title="car", type=ActionTypes.im_back, value="car"),
                    CardAction(title="bus", type=ActionTypes.im_back, value="bus"),
                    CardAction(title="bicycle", type=ActionTypes.im_back, value="bicycle"),
                    CardAction(title="foot", type=ActionTypes.im_back, value="foot"),
                ]
            )
            return await turn_context.send_activity(reply)

        # validate date and wrap it up
        elif flow.last_question_asked2 == Question2.TRANSPORTATION:
            profile.transportation = turn_context.activity.text
            flow.last_question_asked2 = Question2.NONE
            await turn_context.send_activity(
                MessageFactory.text(f"You have selected {profile.transportation} for meeting transportation.")
            )

            flow.CalenderState = State.NONE
            await self._send_welcome_message(turn_context)



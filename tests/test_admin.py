import json
import pytest


def test_add_assignment(test_assignment, test_user_1, runestone_db_tools):
    my_ass = test_assignment("test_assignment", test_user_1.course)
    # Should provide the following to addq_to_assignment
    # -- assignment (an integer)
    # -- question == div_id
    # -- points
    # -- autograde  one of ['manual', 'all_or_nothing', 'pct_correct', 'interact']
    # -- which_to_grade one of ['first_answer', 'last_answer', 'best_answer']
    # -- reading_assignment (boolean, true if it's a page to visit rather than a directive to interact with)
    my_ass.addq_to_assignment(question="subc_b_fitb", points=10)
    print(my_ass.questions())
    db = runestone_db_tools.db
    my_ass.save_assignment()
    res = db(db.assignments.name == "test_assignment").select().first()
    assert res.description == my_ass.description
    assert str(res.duedate.date()) == str(my_ass.due.date())
    my_ass.autograde()
    my_ass.calculate_totals()
    my_ass.release_grades()
    res = db(db.assignments.id == my_ass.assignment_id).select().first()
    assert res.released == True


def test_choose_assignment(test_assignment, test_client, test_user_1):
    my_ass = test_assignment("test_assignment", test_user_1.course)
    my_ass.addq_to_assignment(question="subc_b_fitb", points=10)
    my_ass.description = "Test Assignment Description"
    my_ass.make_visible()
    test_user_1.login()
    test_client.validate(
        "assignments/chooseAssignment.html", "Test Assignment Description"
    )


def test_do_assignment(test_assignment, test_client, test_user_1):
    my_ass = test_assignment("test_assignment", test_user_1.course)
    my_ass.addq_to_assignment(question="subc_b_fitb", points=10)
    my_ass.description = "Test Assignment Description"
    my_ass.make_visible()
    test_user_1.login()
    # This assignment has the fill in the blank for may had a |blank| lamb
    test_client.validate(
        "assignments/doAssignment.html",
        "Mary had a",
        data=dict(assignment_id=my_ass.assignment_id),
    )


def test_question_text(test_client, test_user_1):
    test_user_1.make_instructor()
    test_user_1.login()
    test_client.validate(
        "admin/question_text", "Mary had a", data=dict(question_name="subc_b_fitb")
    )
    test_client.validate(
        "admin/question_text",
        "Error: ",
        data=dict(question_name="non_existant_question"),
    )


def test_removeinstructor(test_user, test_client, test_user_1):
    my_inst = test_user("new_instructor", "password", test_user_1.course)
    my_inst.make_instructor()
    my_inst.login()
    res = test_client.validate("admin/addinstructor/{}".format(test_user_1.user_id))
    assert json.loads(res) == "Success"
    res = test_client.validate("admin/removeinstructor/{}".format(test_user_1.user_id))
    assert json.loads(res) == [True]
    res = test_client.validate("admin/removeinstructor/{}".format(my_inst.user_id))
    assert json.loads(res) == [False]
    res = test_client.validate("admin/addinstructor/{}".format(9999999))
    assert "Cannot add non-existent user " in json.loads(res)


def test_removestudents(test_user, test_client, test_user_1, runestone_db_tools):
    my_inst = test_user("new_instructor", "password", test_user_1.course)
    my_inst.make_instructor()
    my_inst.login()
    res = test_client.validate(
        "admin/removeStudents",
        "Assignments",
        data=dict(studentList=test_user_1.user_id),
    )

    db = runestone_db_tools.db
    res = db(db.auth_user.id == test_user_1.user_id).select().first()
    assert res.active == False


def test_htmlsrc(test_client, test_user_1):
    test_user_1.make_instructor()
    test_user_1.login()
    test_client.validate("admin/htmlsrc", "Mary had a", data=dict(acid="subc_b_fitb"))
    test_client.validate(
        "admin/htmlsrc", "No preview Available", data=dict(acid="non_existant_question")
    )


def test_qbank(test_client, test_user_1):
    test_user_1.make_instructor()
    test_user_1.login()
    qname = "subc_b_fitb"
    res = test_client.validate("admin/questionBank", data=dict(term=qname))
    res = json.loads(res)
    assert qname in res[0]
    res = test_client.validate(
        "admin/questionBank", data=dict(chapter="test_chapter_1")
    )
    res = json.loads(res)
    assert qname in [x[0] for x in res]
    assert len(res) >= 4
    res = test_client.validate("admin/questionBank", data=dict(author="test_author"))
    res = json.loads(res)
    assert qname in [x[0] for x in res]
    assert len(res) == 2


def test_edit_question_does_not_exist(test_user_1, test_client):
    test_user_1.make_instructor()
    test_user_1.login()
    data = {
        "question": "non-existant-question",
        "name": "non-existant-question",
        "htmlsrc": "<p>input</p>",
    }
    res = test_client.validate("admin/edit_question", data=data)
    res = json.loads(res)
    # this does not return a json object if the test succeeds
    assert res == "Could not find question non-existant-question to update"


def test_edit_question_does_not_own(
    test_user_1, test_user, test_client, test_assignment
):
    test_user_1.make_instructor()
    test_user_1.login()
    my_ass = test_assignment("test_assignment", test_user_1.course)
    data = {
        "template": "mchoice",
        "name": "edit_unown_test_question_1",
        "question": "edit_unown_test_question_1",
        "difficulty": 0,
        "tags": None,
        "chapter": "test_chapter_1",
        "subchapter": "Exercises",
        "isprivate": False,
        "assignmentid": my_ass.assignment_id,
        "points": 10,
        "timed": False,
        "htmlsrc": "<p>Hello World</p>",
    }
    test_client.validate("admin/createquestion", data=data)

    test_user_1.logout()
    test_user_2 = test_user(
        "test_user_2", "pass", test_user_1.course, first_name="user", last_name="2"
    )
    test_user_2.make_instructor()
    test_user_2.login()
    data = {
        "question": "edit_unown_test_question_1",
        "name": "edit_unown_test_question_1",
        "questiontext": "Hell0World~",
        "htmlsrc": "<p>Hell0 W0rld</p>",
    }
    res = test_client.validate("admin/edit_question", data=data)
    res = json.loads(res)
    assert (
        res
        == "You do not own this question and are not an editor. Please assign a new unique id"
    )


def test_edit_question_does_not_own_rename(
    test_user_1, test_user, test_client, test_assignment
):
    # Checks to see if replacement name for question collides with existing question that is not owned.
    test_user_1.make_instructor()
    test_user_1.login()
    my_ass = test_assignment("test_assignment", test_user_1.course)
    data = {
        "template": "mchoice",
        "name": "edit_rename_test_question_1",
        "question": "edit_rename_test_question_1",
        "difficulty": 0,
        "tags": None,
        "chapter": "test_chapter_1",
        "subchapter": "Exercises",
        "isprivate": False,
        "assignmentid": my_ass.assignment_id,
        "points": 10,
        "timed": False,
        "htmlsrc": "<p>Hello World</p>",
    }
    test_client.validate("admin/createquestion", data=data)
    data = {
        "template": "mchoice",
        "name": "edit_rename_test_question_2",
        "question": "edit_rename_test_question_2",
        "difficulty": 0,
        "tags": None,
        "chapter": "test_chapter_1",
        "subchapter": "Exercises",
        "isprivate": False,
        "assignmentid": my_ass.assignment_id,
        "points": 10,
        "timed": False,
        "htmlsrc": "<p>Hello World</p>",
    }
    test_client.validate("admin/createquestion", data=data)

    test_user_1.logout()
    test_user_2 = test_user(
        "test_user_2", "pass", test_user_1.course, first_name="user", last_name="2"
    )
    test_user_2.make_instructor()
    test_user_2.login()
    data = {
        "question": "edit_rename_test_question_2",
        "name": "edit_rename_test_question_1",  # overwriting an existant
        "questiontext": "Hell0World~",
        "htmlsrc": "<p>Hell0 W0rld</p>",
    }
    res = test_client.validate("admin/edit_question", data=data)
    res = json.loads(res)
    assert res == "Name taken, you cannot replace a question you did not author"


def test_edit_question_success(test_user_1, test_client, test_assignment):
    test_user_1.make_instructor()
    test_user_1.login()
    my_ass = test_assignment("test_assignment", test_user_1.course)
    data = {
        "template": "mchoice",
        "name": "edit_success_test_question_1",
        "question": "edit_success_test_question_1",
        "difficulty": 0,
        "tags": ["testtag"],
        "chapter": "test_chapter_1",
        "subchapter": "Exercises",
        "isprivate": False,
        "assignmentid": my_ass.assignment_id,
        "points": 10,
        "timed": False,
        "htmlsrc": "<p>Hello World</p>",
    }
    test_client.validate("admin/createquestion", data=data)
    data = {
        "question": "edit_success_test_question_1",
        "name": "edit_success_test_question_1",
        "questiontext": "Hello!",
        "htmlsrc": "<p>Hello!</p>",
    }
    res = test_client.validate("admin/edit_question", data=data)
    res = json.loads(res)
    assert res == "Success - Edited Question Saved"


def test_gettemplate(test_user_1, test_client):
    test_user_1.make_instructor()
    test_user_1.login()
    dirlist = ["activecode", "mchoice", "fillintheblank"]
    for d in dirlist:
        res = test_client.validate("admin/gettemplate/{}".format(d))
        res = json.loads(res)
        assert res
        assert d in res["template"]


def test_question_info(test_assignment, test_user_1, test_client):
    test_user_1.make_instructor()
    test_user_1.login()
    my_ass = test_assignment("test_assignment", test_user_1.course)
    my_ass.addq_to_assignment(question="subc_b_fitb", points=10)
    res = test_client.validate(
        "admin/getQuestionInfo",
        data=dict(assignment=my_ass.assignment_id, question="subc_b_fitb"),
    )
    res = json.loads(res)
    assert res
    assert res["code"]
    assert res["htmlsrc"]


def test_create_question(test_assignment, test_user_1, runestone_db_tools, test_client):
    test_user_1.make_instructor()
    test_user_1.login()
    my_ass = test_assignment("test_assignment", test_user_1.course)
    data = {
        "template": "mchoice",
        "name": "test_question_1",
        "question": "This is fake text for a fake question",
        "difficulty": 0,
        "tags": None,
        "chapter": "test_chapter_1",
        "subchapter": "Exercises",
        "isprivate": False,
        "assignmentid": my_ass.assignment_id,
        "points": 10,
        "timed": False,
        "htmlsrc": "<p>Hello World</p>",
    }
    res = test_client.validate("admin/createquestion", data=data)
    res = json.loads(res)
    assert res
    assert res["test_question_1"]

    db = runestone_db_tools.db
    row = db(db.questions.id == res["test_question_1"]).select().first()

    assert row["question"] == "This is fake text for a fake question"


def test_get_assignment(test_assignment, test_user_1, test_client):
    test_user_1.make_instructor()
    test_user_1.login()
    my_ass = test_assignment("test_assignment", test_user_1.course)
    my_ass.addq_to_assignment(question="subc_b_fitb", points=10)

    res = test_client.validate(
        "admin/get_assignment", data=dict(assignmentid=my_ass.assignment_id)
    )

    res = json.loads(res)
    assert res
    assert res["questions_data"]


@pytest.mark.parametrize("assign_id", [(-1), (0)])
def test_copy_assignment(
    assign_id, test_assignment, test_client, test_user_1, runestone_db_tools
):
    test_user_1.make_instructor()
    test_user_1.login()
    course1_id = test_user_1.course.course_id
    my_ass = test_assignment("test_assignment", test_user_1.course)
    # Should provide the following to addq_to_assignment
    # -- assignment (an integer)
    # -- question == div_id
    # -- points
    # -- autograde  one of ['manual', 'all_or_nothing', 'pct_correct', 'interact']
    # -- which_to_grade one of ['first_answer', 'last_answer', 'best_answer']
    # -- reading_assignment (boolean, true if it's a page to visit rather than a directive to interact with)
    my_ass.addq_to_assignment(question="subc_b_fitb", points=10)
    print(my_ass.questions())
    db = runestone_db_tools.db
    my_ass.save_assignment()

    course_3 = runestone_db_tools.create_course(
        "test_course_3", base_course="test_course_1"
    )
    test_user_1.make_instructor(course_3.course_id)
    db(db.auth_user.id == test_user_1.user_id).update(
        course_id=course_3.course_id, course_name="test_course_3"
    )
    db.commit()
    test_user_1.logout()
    test_user_1.login()
    if assign_id == 0:
        assign_id = my_ass.assignment_id
    res = test_client.validate(
        "admin/copy_assignment",
        data=dict(oldassignment=assign_id, course="test_child_course_1"),
    )
    assert res == "success"

    rows = db(db.assignments.name == "test_assignment").count()
    assert rows == 2

    row = (
        db(db.assignments.name == "test_assignment")
        .select(orderby=~db.assignments.id)
        .first()
    )
    rows = db(db.assignment_questions.assignment_id == row.id).count()
    assert rows == 1


def test_flag_question(test_assignment, test_user_1, test_client, runestone_db_tools):
    test_user_1.make_instructor()
    test_user_1.login()

    res = test_client.validate(
        "admin/flag_question", data=dict(question_name="subc_b_fitb")
    )

    res = json.loads(res)
    assert res
    assert res["status"] == "success"

    db = runestone_db_tools.db

    assert db(db.questions.name == "subc_b_fitb").select().first().review_flag


def test_get_assignment_release_states(test_assignment, test_client, test_user_1):
    my_ass = test_assignment("test_assignment", test_user_1.course)
    my_ass.addq_to_assignment(question="subc_b_fitb", points=10)
    my_ass.save_assignment()
    my_ass.autograde()
    my_ass.calculate_totals()
    my_ass.release_grades()

    res = test_client.validate("admin/get_assignment_release_states")
    res = json.loads(res)

    assert res["test_assignment"] == True


def test_delete_assignment_question(test_assignment, test_client, test_user_1):
    test_user_1.make_instructor()
    test_user_1.login()
    my_ass = test_assignment("test_assignment", test_user_1.course)
    my_ass.addq_to_assignment(question="subc_b_fitb", points=10)
    assert len(my_ass.questions()) == 1

    _ = test_client.validate(
        "admin/delete_assignment_question",
        data=dict(name="subc_b_fitb", assignment_id=my_ass.assignment_id),
    )

    assert len(my_ass.questions()) == 0


def test_reorder_assignment_questions(
    test_assignment, test_client, test_user_1, runestone_db_tools
):
    test_user_1.make_instructor()
    test_user_1.login()
    my_ass = test_assignment("test_assignment", test_user_1.course)
    my_ass.addq_to_assignment(question="subc_b_fitb", points=10)
    my_ass.addq_to_assignment(question="subc_b_1", points=10)

    questions = my_ass.questions()
    question_id_one, name_one = questions[0]
    question_id_two, name_two = questions[1]

    db = runestone_db_tools.db

    res = (
        db(
            (db.assignment_questions.assignment_id == my_ass.assignment_id)
            & (db.assignment_questions.question_id == question_id_one)
        )
        .select(db.assignment_questions.sorting_priority)
        .first()
    )

    assert res.sorting_priority == 1

    res = (
        db(
            (db.assignment_questions.assignment_id == my_ass.assignment_id)
            & (db.assignment_questions.question_id == question_id_two)
        )
        .select(db.assignment_questions.sorting_priority)
        .first()
    )

    assert res.sorting_priority == 2

    res = test_client.validate(
        "admin/reorder_assignment_questions",
        data={
            "names[]": ["subc_b_1", "subc_b_fitb"],
            "assignment_id": my_ass.assignment_id,
        },
    )
    assert json.loads(res) == "Reordered in DB"

    res = (
        db(
            (db.assignment_questions.assignment_id == my_ass.assignment_id)
            & (db.assignment_questions.question_id == question_id_one)
        )
        .select(db.assignment_questions.sorting_priority)
        .first()
    )
    assert res.sorting_priority == 2

    res = (
        db(
            (db.assignment_questions.assignment_id == my_ass.assignment_id)
            & (db.assignment_questions.question_id == question_id_two)
        )
        .select(db.assignment_questions.sorting_priority)
        .first()
    )

    assert res.sorting_priority == 1

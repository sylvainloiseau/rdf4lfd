from rico_namespace import RICO, RicoOwl
from owlready2 import ThingClass

class TestRicoNamespace:
    def test_rico(request):
        pass

class TestRicoOwl:

    @staticmethod
    def test_rico_get_classes(capsys, request):
        rico = RicoOwl()
        classes = rico.get_classes()
        with capsys.disabled():
            l = 0
            for c in classes:
                print(f"class: {c}")
                print(type(c))
                print(str(c))
                l+=1
            print(f"{l} classes found")
            

    @staticmethod
    def test_rico_get_info(capsys, request):
        rico = RicoOwl()
        classes = rico.get_classes()
        with capsys.disabled():
            for c in classes:
                print(f"-----------------------")
                print(f"class: {c}")
                for i in ThingClass.instances(c):
                    print(f"\tinstance: {i}")
                for p in ThingClass.get_class_properties(c):
                    print(f"\tproperty: {p}")
                for p in rico.onto.object_properties():
                    print(f"\tobject property: {p}")
                for p in rico.onto.data_properties():
                    print(f"\tdata property: {p}")

                 


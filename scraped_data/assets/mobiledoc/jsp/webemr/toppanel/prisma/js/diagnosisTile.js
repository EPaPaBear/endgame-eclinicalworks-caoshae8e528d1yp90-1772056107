angular.module('prisma.clinicalInsights.diagnosisTile', []).directive('diagnosisTile', () => {
    return {
        restrict: 'E',
        scope: {
            options: '=',
            header:"@",
            ordered:"@",
            duplicateProblems:"="
        },
        templateUrl : '/mobiledoc/jsp/webemr/toppanel/prisma/template/diagnosisTile.html',
        link: dx => {
            const cmp = (a, b) => (a > b) - (a < b);
            const MMDDYYYY = "MM/DD/YYYY";
            const isDateValid = (date, format) => moment(date, format??MMDDYYYY, true).isValid()
            let listener = dx.$watch('options', () => {
                dx.problems = (dx.ordered === 'true') ?prepareProblems(dx.options):dx.options;
                let hiddenProblems = dx.problems.filter(prob=>(!prob.show));
                dx.problems = dx.problems.filter(prob=>(prob.show));
                dx.problems = dx.problems.filter(prob => (prob.isException===0))
                dx.problems = dx.problems?.map(m => { return {...m, displayCode : m?.codes?.find(x => x?.code && x?.codesystem )}})
                dx.problems = prepareUniqueProblems(dx.problems);
            });

            const prepareUniqueProblems = (problems)  =>{
                let priority = { '10': 3, 'sn': 2, '9': 1 };
                let uniqueProblemLst = [];
                for(let i = 0; i < problems.length; i++) {
                    let item = problems[i];
                    let index = uniqueProblemLst.findIndex(obj => obj.itemName === item.itemName && obj.onset === item.onset && obj.source === item.source);
                    if(index === -1) {
                        uniqueProblemLst.push(item);
                    } else {
                        let existingItem = uniqueProblemLst[index];
                        if(priority[item.displayCode.codesystem] > priority[existingItem.displayCode.codesystem]) {
                            uniqueProblemLst[index] = item;
                        }
                    }
                }
                return uniqueProblemLst;
            }

            dx.$on("$destroy", function(){
                listener();
            });
            const prepareProblems = (problems) => [
                ...problems.filter(x => isDateValid(x?.onset)).sort((a,b) => moment(b.onset, MMDDYYYY) - moment(a.onset, MMDDYYYY)),
                ...problems.filter(x => !isDateValid(x?.onset)).sort((a,b) => cmp(b.itemName, a.itemName))
            ]
        }
    };
})
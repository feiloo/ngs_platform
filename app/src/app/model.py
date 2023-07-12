from typing import Optional, Literal, List
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field
from uuid import UUID
import json

# some runs are missing information because of device or network failure
# for those only the fastq data is available
runformat: ['miseq_0', 'only_fastq']

DATA_MODEL_VERSION = '0.0.1'

# based on the ordercodes of "NGS_Panel_Abdeckung_MolPath.docx"
panel_types = [
        'invalid', 
        'NGS DNA Lungenpanel', 
        'NGS oncoHS', 
        'NGS BRCAness', 
        'NGS RNA Sarkom', 
        'NGS RNA Fusion Lunge', 
        'NGS PanCancer'
        ]

PanelType = Literal[
        'invalid', 
        'NGS DNA Lungenpanel', 
        'NGS oncoHS', 
        'NGS BRCAness', 
        'NGS RNA Sarkom', 
        'NGS RNA Fusion Lunge', 
        'NGS PanCancer'
        ]

primerMixes = {
        'C1': {
            'panel type': 'unknown',
            'primers': [],
            }
        }

# examination identifiers used in filemaker
filemaker_examination_types = [
        'DNA Lungenpanel Qiagen - kein nNGM Fall',
        'DNA Panel ONCOHS',
        'DNA PANEL ONCOHS (Mamma)', # basically calls ONCOHS,
        'DNA PANEL ONCOHS (Melanom)',# basically calls ONCOHS
        'DNA PANEL ONCOHS (Colon)',# basically calls ONCOHS
        'DNA PANEL ONCOHS (GIST)',# basically calls ONCOHS
        'DNA PANEL 522', # research panel
        'DNA PANEL Multimodel PanCancer DNA',
        'DNA PANEL Multimodel PanCancer RNA',
        'NNGM Lunge Qiagen',
        'RNA Fusion Lunge',
        'RNA Sarkompanel',
        ]


class BaseDocument(BaseModel):
    id: str
    rev: Optional[str] = None
    data_model_version: str = DATA_MODEL_VERSION
    document_type: str
    dirty: bool = True
    ignore_dirty: bool = False

    def __init__(self, map_id: bool, *args, **kwargs):
        d = kwargs
        if map_id==True:
            if '_id' in d:
                d['id'] = d.pop('_id')
            if '_rev' in d:
                d['rev'] = d.pop('_rev')

        super().__init__(*args, **d)

    def to_dict(self):
        # convert to serializable dict
        d = json.loads(self.json())
        d.pop('id')
        d.pop('rev')
        if self.id is not None:
            d['_id'] = self.id
        if self.rev is not None:
            d['_rev'] = self.rev
        return d

    def from_dict(self, d):
        m = type(self)(True,**d)
        return m

    class Config:
        validate_assignment = True
        frozen = True


class PipelineLogs(BaseModel):
    stdout: str
    stderr: str


class PipelineRun(BaseDocument):
    document_type: str = 'pipeline_run'
    created_time: datetime
    input_samples: List[Path]
    workflow: str
    status: Literal['running', 'error', 'successful']
    logs: PipelineLogs


class SequencerRun(BaseDocument):
    document_type: str = 'sequencer_run'
    original_path: Path
    name_dirty: bool
    parsed: dict
    indexed_time: datetime
    state: str = 'unfinished'
    outputs: List[Path]


class SampleBlock(BaseDocument):
    patient_ref: int

class SampleCuts(BaseDocument):
    block_ref: int

class SampleExtraction(BaseDocument):
    sample_cut_ref: int
    molnr: str

class SequencerInputSample(BaseDocument):
    document_type: str = 'sequencer_input_sample'
    kit: str
    molnr: str # references sample-extraction
    concentration: float
    index1: str
    index2: str
    sample_volume: float
    sample_water: float
    final: bool = False
    repetition: bool = False

class TrackingForm(BaseDocument):
    document_type: str = 'tracking_form'
    created_time: datetime
    samples: List[SequencerInputSample]
    

class MolYearNumber(BaseModel):
    molnumber: int
    molyear: int


class Examination(BaseDocument):
    ''' medical examination/case '''
    document_type: str = 'examination'
    examinationtype: str
    #examination_requester: Union[Literal['internal'], str]
    started_date: datetime
    sequencer_runs: List[str]
    pipeline_runs: List[str]
    filemaker_record: Optional[dict] = None
    last_sync_time: Optional[datetime] = None
    result: Optional[str] = None
    patient: Optional[str] = None

    
class Person(BaseDocument):
    names: dict[str,str]

class Patient(Person):
    document_type: str = 'patient'
    #mp_nr: str
    examinations: List[str]
    birthdate: Optional[datetime]
    gender: str

class Pathologist(Person):
    short_name: str

class Clinician(Person):
    short_name: str

class Result(BaseModel):
    description: str

document_types = {
        'sequencer_run': SequencerRun, 
        'pipeline_run': PipelineRun, 
        'examination': Examination, 
        'patient': Patient
        }

#we need to create different taxonomical concepts for "workflow"
# patho_workflow is the generalization of a ngs_panel 
# that also includes manual steps like library preparation
# this will be modeled by the according manual descriptions
# versioned and available
# in human readable form like html, pdf, word

# sequence_analysis_workflow is the workflow that specifically
# uses code in wdl format to automatically analyse mutations

# model for a pathology examination

# steps can be repeated, if for example samples are contaminated

# step started and finished are usefull, because multiple steps 
# could run concurrently
'''
database_stub = [
        {
        "_id": "1",
        "case_ref": {
            "molnr":2132, 
            "year":2022, 
            "examinationtype":"oncohs",
            },
        "workflow": {
            "patho_workflow_uri": "uri",
            "steps": [
                {   "step_id": "patho_workflow_step_pipetting",
                    "step_data": {
                        "kit":"rna 340",
                        "original_concentration (ng/ul)":116.0, 
                        "diluted aqua (ul)":3.71, 
                        "index1":"IL-N728",
                        "index2":"IL-S502",
                        },
                    "step_started": "date",
                    "step_finished": "date",
                },
                {
                    "step_id": "patho_workflow_step_validate_pipetting"
                    "step_started": "date",
                    "step_finished": "date",
                },
                {   "step_id": "patho_workflow_step_pipetting_repeat",
                    "step_data": {
                        "original_concentration (ng/ul)":116.0, 
                        "diluted aqua (ul)":3.71, 
                        "repitition": 1,
                        },
                    "step_started": "date",
                    "step_finished": "date",
                },
                {   "step_id": "sequence_analysis",
                    "step_data": "..."
                    "step_started": "date",
                    "step_finished": "date",
                }
                ]
            }
        }]
'''
